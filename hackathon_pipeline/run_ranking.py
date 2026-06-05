import json
import time
import os
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import lightgbm as lgb
from feature_extractor import extract_recruiter_features, get_lexical_scores
from sentence_transformers import SentenceTransformer

def get_docx_text(path):
    z = zipfile.ZipFile(path)
    xml_content = z.read('word/document.xml')
    z.close()
    tree = ET.XML(xml_content)
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join(''.join(n.text for n in p.iter(w+'t') if n.text) for p in tree.iter(w+'p') if any(n.text for n in p.iter(w+'t')))

def run_pipeline():
    start_time = time.time()
    
    # 1. Load resources
    print("Loading pre-computed embeddings and models...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Check if embeddings are done, otherwise fallback to mock for now
    if os.path.exists("candidate_embeddings.npy"):
        embeddings = np.load("candidate_embeddings.npy")
        with open("candidate_embeddings_ids.json", "r") as f:
            candidate_ids = json.load(f)
    else:
        # Failsafe if running before embeddings finish
        print("Embeddings not found. Please wait for offline_embedder to finish.")
        return
        
    ranker = lgb.Booster(model_file="lgbm_ranker.txt")
    
    # 2. Parse JD
    jd_path = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx"
    if not os.path.exists(jd_path):
        jd_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx"
    jd_text = get_docx_text(jd_path)
    
    # 3. Stage 1: Fast Retrieval (Hybrid)
    print("Encoding query and performing hybrid retrieval...")
    query_emb = embedder.encode([jd_text], convert_to_numpy=True)[0].astype(np.float16)
    similarities = embeddings.dot(query_emb)
    
    # Get top 5000 semantic indices
    top_k_semantic = 5000
    top_sem_indices = np.argsort(similarities)[::-1][:top_k_semantic]
    top_sem_ids = set([candidate_ids[i] for i in top_sem_indices])
    
    # Pass all 100k texts for fast BM25? No, that requires reading the JSONL first.
    # Let's read the JSONL, building a lightweight mapping, and checking if they are in top_sem_ids.
    # To truly do BM25 on all 100k, we must load all 100k summaries. 
    # For speed in 5 mins, we will do BM25 on a slightly reduced set, or just read all.
    # Actually, reading 100k JSONs takes ~1.5s in Python.
    print("Scanning dataset...")
    candidates_path = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(candidates_path):
        candidates_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
        
    all_cands = []
    # Optimization: Read all, store minimal info for BM25
    corpus_texts = []
    cand_index_map = []
    
    with open(candidates_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip(): continue
            try:
                cand = json.loads(line) # Proper JSON parsing to avoid index bugs
                cid = cand.get("candidate_id")
                
                # If it's in semantic top 5000, keep the full object
                if cid in top_sem_ids:
                    all_cands.append(cand)
                else:
                    # Also collect it for BM25 global calculation
                    all_cands.append(cand)
            except:
                pass
                
    # Fast BM25 on all
    print("Calculating Lexical BM25 Scores...")
    for cand in all_cands:
        text = str(cand.get('headline', '')) + " " + str(cand.get('summary', ''))
        corpus_texts.append(text)
        
    bm25_all = get_lexical_scores(jd_text, corpus_texts)
    
    # Get Top 5000 BM25 ids
    top_bm25_indices = np.argsort(bm25_all)[::-1][:5000]
    top_bm25_ids = set([all_cands[i]['candidate_id'] for i in top_bm25_indices])
    
    # Union of Semantic Top 5k and BM25 Top 5k (Max 10k)
    union_ids = top_sem_ids.union(top_bm25_ids)
    
    print(f"Union retrieval yielded {len(union_ids)} candidates. Extracting full records...")
    
    # Filter the objects down to just the union
    top_records = [c for c in all_cands if c['candidate_id'] in union_ids]
    df = pd.DataFrame(top_records)
    
    # Attach semantic and bm25 scores to the df
    # Map array indices
    cid_to_sim = {candidate_ids[i]: similarities[i] for i in range(len(similarities))}
    cid_to_bm25 = {all_cands[i]['candidate_id']: bm25_all[i] for i in range(len(all_cands))}
    
    df['semantic_sim'] = [cid_to_sim.get(cid, 0) for cid in df['candidate_id']]
    df['bm25_score'] = [cid_to_bm25.get(cid, 0) for cid in df['candidate_id']]
    
    # 5. Stage 3: Advanced Recruiter Feature Extraction
    print("Extracting heavy recruiter features...")
    features_df = extract_recruiter_features(df)
    features_df['semantic_sim'] = df['semantic_sim']
    features_df['bm25_score'] = df['bm25_score']
    
    # Hard Filters based on Consistency and Disqualifiers
    valid_mask = (
        (features_df['career_consistency_score'] > 0) & 
        (features_df['timeline_consistency_score'] > 0)
    )
    features_df = features_df[valid_mask].copy()
    valid_cids = df.loc[valid_mask, 'candidate_id'].values
    valid_records = df[valid_mask].copy()
    
    # 6. Stage 4: LightGBM Inference
    print("Running LightGBM LambdaRank inference...")
    feature_cols = [
        'semantic_sim', 'bm25_score',
        'retrieval_experience_score', 'ranking_experience_score', 'embedding_experience_score',
        'vector_db_score', 'evaluation_framework_score', 'production_ml_score',
        'hireability_score', 'career_consistency_score', 'timeline_consistency_score',
        'recruiter_interest_score', 'startup_readiness_score', 'leadership_score',
        'product_ownership_score', 'synthetic_risk_score', 'role_progression_score',
        'jd_disqualifier_penalty', 'github_activity_score'
    ]
    
    X = features_df[feature_cols]
    scores = ranker.predict(X)
    
    # 7. Stage 5: Select Top 100 & Generate Recruiter Reasoning
    print("Generating explanations for Top 100...")
    results = pd.DataFrame({
        'candidate_id': valid_cids,
        'score': scores
    })
    
    if 'years_of_experience' not in valid_records.columns:
        valid_records['years_of_experience'] = 0
        
    results = pd.concat([results.reset_index(drop=True), X.reset_index(drop=True), valid_records.reset_index(drop=True)[['years_of_experience']]], axis=1)
    
    top_100 = results.sort_values(by=['score', 'candidate_id'], ascending=[False, True]).head(100).copy()
    top_100['rank'] = range(1, 101)
    
    reasonings = []
    for idx, row in top_100.iterrows():
        exp = row.get('years_of_experience', 0)
        ret = row.get('retrieval_experience_score', 0)
        vec = row.get('vector_db_score', 0)
        prod = row.get('production_ml_score', 0)
        hire = row.get('hireability_score', 0)
        start = row.get('startup_readiness_score', 0)
        
        reasoning = f"Strong ML Engineer fit with {exp} yrs exp. "
        
        if ret > 2 and vec > 1:
            reasoning += "Extensive background building retrieval and ranking systems with production vector-search infrastructure. "
        elif ret > 1:
            reasoning += "Demonstrated experience in search and retrieval systems. "
            
        if prod > 2:
            reasoning += "Proven ability to deploy models and scale production ML systems. "
            
        if start > 2:
            reasoning += "High startup readiness with cross-functional ownership. "
            
        if hire > 3:
            reasoning += "Exceptional recruiter engagement signals and hireability. "
            
        reasonings.append(reasoning.strip())
        
    top_100['reasoning'] = reasonings
    
    final_out = top_100[['candidate_id', 'rank', 'score', 'reasoning']].copy()
    final_out['score'] = final_out['score'].apply(lambda x: f"{x:.4f}")
    
    final_out.to_csv("submission.csv", index=False)
    
    elapsed = time.time() - start_time
    print(f"Pipeline finished successfully in {elapsed:.2f} seconds!")
    print("Output saved to submission.csv")

if __name__ == "__main__":
    run_pipeline()
