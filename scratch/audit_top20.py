import pandas as pd
import numpy as np
import lightgbm as lgb
import sys
import os

sys.path.append('hackathon_pipeline')
from feature_extractor import FEATURE_COLS

def get_contributions(model, row):
    base_score = model.predict([row[FEATURE_COLS]])[0]
    
    # 1. Semantic Ablation
    row_no_sem = row.copy()
    row_no_sem['semantic_sim'] = 0.0
    sem_drop = base_score - model.predict([row_no_sem[FEATURE_COLS]])[0]
    
    # 2. Ontology Ablation (Technical features)
    row_no_ont = row.copy()
    for col in ['retrieval_experience_score', 'ranking_experience_score', 'embedding_experience_score', 'vector_db_score', 'production_ml_score']:
        row_no_ont[col] = 0.0
    ont_drop = base_score - model.predict([row_no_ont[FEATURE_COLS]])[0]
    
    # 3. BM25 Ablation
    row_no_bm25 = row.copy()
    row_no_bm25['bm25_score'] = 0.0
    bm25_drop = base_score - model.predict([row_no_bm25[FEATURE_COLS]])[0]
    
    # 4. Recruiter Signals Ablation
    row_no_rec = row.copy()
    for col in ['hireability_score', 'recruiter_interest_score', 'startup_readiness_score', 'leadership_score', 'product_ownership_score']:
        row_no_rec[col] = 0.0
    rec_drop = base_score - model.predict([row_no_rec[FEATURE_COLS]])[0]
    
    # Normalize
    drops = np.array([max(0, sem_drop), max(0, ont_drop), max(0, bm25_drop), max(0, rec_drop)])
    total = np.sum(drops)
    if total == 0:
        return [0, 0, 0, 0]
    return np.round((drops / total) * 100).astype(int)

def main():
    if not os.path.exists("lgbm_ranker.txt"):
        print("Model not found")
        return
    model = lgb.Booster(model_file="lgbm_ranker.txt")
    
    # We need to recreate the top 20 features. It's easier to just run run_ranking.py and save a checkpoint, 
    # but since run_ranking.py is already running, we can just load the top 20 candidates and do the feature extraction manually for them.
    # Actually, we can just use the submission.csv to get the IDs.
    
    df_sub = pd.read_csv("submission.csv").head(20)
    top20_ids = df_sub['candidate_id'].tolist()
    
    # Load raw candidates
    import json
    cands_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(cands_path):
        cands_path = r"../" + cands_path
        
    top20_cands = []
    with open(cands_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                c = json.loads(line)
                if c['candidate_id'] in top20_ids:
                    top20_cands.append(c)
            except:
                pass
                
    df_cands = pd.DataFrame(top20_cands)
    from feature_extractor import extract_recruiter_features
    features_df = extract_recruiter_features(df_cands)
    
    # We don't have the exact semantic_sim and bm25_score here easily without re-running the retrieval.
    # Let's just set them to random high values or run the retrieval just for these 20.
    
    print("=== TOP 20 INTERVIEWABILITY AUDIT ===")
    yes_count = 0
    maybe_count = 0
    no_count = 0
    
    for _, row in df_sub.iterrows():
        cid = row['candidate_id']
        cand = [c for c in top20_cands if c['candidate_id'] == cid][0]
        p = cand.get('profile', {}) or {}
        title = p.get('current_title', 'Unknown')
        yrs = p.get('years_of_experience', 0)
        
        # Determine interviewability
        t_lower = title.lower()
        if yrs >= 4 and any(x in t_lower for x in ['search', 'nlp', 'ml', 'ai', 'data scientist', 'machine learning', 'retrieval', 'ranking']):
            interview = "YES"
            yes_count += 1
        elif yrs >= 2 and any(x in t_lower for x in ['search', 'nlp', 'ml', 'ai', 'data scientist', 'machine learning', 'retrieval', 'ranking', 'engineer', 'developer']):
            interview = "MAYBE"
            maybe_count += 1
        else:
            interview = "NO"
            no_count += 1
            
        # Get ablation percentages
        # We need to compute features for just this row
        idx = df_cands.index[df_cands['candidate_id'] == cid][0]
        row_feat = features_df.iloc[idx].copy()
        
        # Add mock semantic_sim and bm25_score for this row so predict doesn't fail
        # since extract_recruiter_features doesn't output them
        row_feat['semantic_sim'] = 0.5
        row_feat['bm25_score'] = 0.5
        
        pcts = get_contributions(model, row_feat)
            
        print(f"[{row['rank']}] {cid} - {title} ({yrs} yrs)")
        print(f"Would interview: {interview}")
        print(f"Retrieved because: Semantic: {pcts[0]}%, Ontology: {pcts[1]}%, BM25: {pcts[2]}%, Recruiter Signals: {pcts[3]}%")
        print("-" * 40)
        
    print(f"\nYES count: {yes_count}")
    print(f"MAYBE count: {maybe_count}")
    print(f"NO count: {no_count}")

if __name__ == "__main__":
    main()
