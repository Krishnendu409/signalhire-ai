import json
import time
import os
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import lightgbm as lgb
from feature_extractor import calculate_fraud_risk, extract_behavioral_features, get_lexical_scores
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
    embeddings = np.load("candidate_embeddings.npy")
    with open("candidate_embeddings_ids.json", "r") as f:
        candidate_ids = json.load(f)
        
    ranker = lgb.Booster(model_file="lgbm_ranker.txt")
    
    # 2. Parse JD
    jd_path = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx"
    if not os.path.exists(jd_path):
        jd_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx"
    jd_text = get_docx_text(jd_path)
    
    # 3. Stage 1: Fast Retrieval (Semantic)
    print("Encoding query and performing semantic retrieval...")
    query_emb = embedder.encode([jd_text], convert_to_numpy=True)[0].astype(np.float16)
    
    # Dot product similarity
    similarities = embeddings.dot(query_emb)
    
    # Get top 2000 indices
    top_k = 2000
    top_indices = np.argsort(similarities)[::-1][:top_k]
    top_ids = set([candidate_ids[i] for i in top_indices])
    
    # Store similarities for the top IDs
    sim_dict = {candidate_ids[i]: similarities[i] for i in top_indices}
    
    # 4. Stage 2: Load JSONs for Top 2000
    print(f"Extracting JSON records for top {top_k} candidates...")
    top_records = []
    candidates_path = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(candidates_path):
        candidates_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
        
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            cand_id = line[17:29] # Fast string slice optimization to peek at ID, e.g. {"candidate_id": "CAND_1234567"
            if cand_id in top_ids:
                top_records.append(json.loads(line))
            elif "CAND_" in line[:50]:
                # Fallback if slice is slightly off
                cand = json.loads(line)
                if cand.get("candidate_id") in top_ids:
                    top_records.append(cand)
                    
    df = pd.DataFrame(top_records)
    
    # 5. Stage 3: Feature Extraction
    print("Extracting features and running dataset forensics...")
    df = calculate_fraud_risk(df)
    features_df = extract_behavioral_features(df)
    
    # Attach semantic similarity
    features_df['semantic_sim'] = [sim_dict.get(cid, 0) for cid in df['candidate_id']]
    
    # Calculate BM25 only on the top 2000 to save time
    corpus_texts = []
    for idx, row in df.iterrows():
        summary = row.get('summary', '') or ''
        skills = " ".join([s.get('name', '') for s in row.get('skills', [])])
        corpus_texts.append(f"{summary} {skills}")
    features_df['bm25_score'] = get_lexical_scores(jd_text, corpus_texts)
    
    # Drop honeypots
    valid_mask = (df['fraud_risk_score'] < 1.0) & (features_df['notice_period_days'] <= 60)
    features_df = features_df[valid_mask].copy()
    valid_cids = df.loc[valid_mask, 'candidate_id'].values
    valid_records = df[valid_mask].copy()
    
    # 6. Stage 4: LightGBM Inference
    print("Running LightGBM LambdaRank inference...")
    feature_cols = [
        'semantic_sim', 'bm25_score', 'recency_decay_score', 
        'avg_tenure_months', 'product_company_ratio', 
        'recruiter_response_rate', 'github_activity_score', 
        'notice_period_days', 'fraud_risk_score'
    ]
    
    X = features_df[feature_cols]
    scores = ranker.predict(X)
    
    # 7. Stage 5: Select Top 100 & Generate Reasoning
    print("Generating explanations for Top 100...")
    results = pd.DataFrame({
        'candidate_id': valid_cids,
        'score': scores
    })
    
    # Join features back for reasoning text
    results = pd.concat([results.reset_index(drop=True), X.reset_index(drop=True), valid_records.reset_index(drop=True)[['years_of_experience']]], axis=1)
    
    # Sort and take top 100
    top_100 = results.sort_values(by=['score', 'candidate_id'], ascending=[False, True]).head(100).copy()
    top_100['rank'] = range(1, 101)
    
    # Template-based NLG
    reasonings = []
    for idx, row in top_100.iterrows():
        exp = row.get('years_of_experience', 0)
        rr = row.get('recruiter_response_rate', 0)
        gh = row.get('github_activity_score', 0)
        
        reasoning = f"Strong ML Engineer fit with {exp} yrs exp. "
        if gh > 30:
            reasoning += f"High GitHub activity ({gh}). "
        if rr > 0.7:
            reasoning += f"Highly responsive ({rr*100:.0f}%). "
            
        reasoning += "Zero fraud risk indicators."
        reasonings.append(reasoning.strip())
        
    top_100['reasoning'] = reasonings
    
    # Output
    final_out = top_100[['candidate_id', 'rank', 'score', 'reasoning']].copy()
    # Format score to 4 decimals
    final_out['score'] = final_out['score'].apply(lambda x: f"{x:.4f}")
    
    final_out.to_csv("submission.csv", index=False)
    
    elapsed = time.time() - start_time
    print(f"Pipeline finished successfully in {elapsed:.2f} seconds!")
    print("Output saved to submission.csv")

if __name__ == "__main__":
    run_pipeline()
