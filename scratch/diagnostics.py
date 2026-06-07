import json
import pandas as pd
import numpy as np

def run_diagnostics():
    import sys
    sys.path.append(r"C:\Users\krish\Documents\signalhire")
    from hackathon_pipeline.feature_extractor import extract_recruiter_features, FEATURE_COLS
    
    print("Loading all candidates...")
    path = r"C:\Users\krish\Documents\signalhire\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
    
    all_cands = {}
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    c = json.loads(line)
                    all_cands[c['candidate_id']] = c
                    records.append(c)
                except:
                    pass
                    
    print(f"Loaded {len(records)} total candidates.")
    
    # Load submission to get top 100
    try:
        sub_df = pd.read_csv(r"C:\Users\krish\Documents\signalhire\submission.csv")
        top_100_ids = sub_df['candidate_id'].head(100).tolist()
    except Exception as e:
        print("Could not load submission.csv. Are you sure the pipeline has finished?")
        return
        
    top_100_records = [all_cands[cid] for cid in top_100_ids if cid in all_cands]
    
    # Sample 1000 from all candidates for the baseline
    import random
    random.seed(42)
    baseline_records = random.sample(records, min(1000, len(records)))
    
    print("Extracting features for Top 100...")
    top_100_df = extract_recruiter_features(pd.DataFrame(top_100_records))
    
    print("Extracting features for Baseline (1000 random)...")
    baseline_df = extract_recruiter_features(pd.DataFrame(baseline_records))
    
    print("\n=========================================")
    print("FEATURE DISTRIBUTION DIAGNOSTICS")
    print("=========================================\n")
    print(f"{'Feature':<30} | {'Top 100 Avg':<12} | {'Baseline Avg':<12} | {'Ratio (Top/Base)':<15}")
    print("-" * 75)
    
    for col in FEATURE_COLS:
        if col in ['bm25_score', 'semantic_sim', 'rrf_score']:
            continue # We can't extract these from candidate JSON alone
            
        if col in top_100_df.columns and col in baseline_df.columns:
            t_mean = top_100_df[col].mean()
            b_mean = baseline_df[col].mean()
            ratio = (t_mean / (b_mean + 1e-9)) if b_mean > 0 else float('inf')
            print(f"{col:<30} | {t_mean:<12.4f} | {b_mean:<12.4f} | {ratio:<15.2f}")

    print("\n=========================================")
    print("TOP 20 CANDIDATE AUDIT (WHY ARE THEY HERE?)")
    print("=========================================\n")
    
    # We will print the top 20 candidates and their specific defining scores
    for i, row in top_100_df.head(20).iterrows():
        cid = top_100_ids[i]
        print(f"Rank {i+1} | Candidate: {cid}")
        print(f"  Retrieval Score: {row.get('retrieval_experience_score', 0):.2f}")
        print(f"  Ranking Score:   {row.get('ranking_experience_score', 0):.2f}")
        print(f"  Vector DB Score: {row.get('vector_db_score', 0):.2f}")
        print(f"  Evaluation Score:{row.get('evaluation_framework_score', 0):.2f}")
        print(f"  Hireability:     {row.get('hireability_score', 0):.2f}")
        print(f"  Consistency:     {row.get('career_consistency_score', 0):.2f}")
        print("-" * 40)

if __name__ == "__main__":
    run_diagnostics()
