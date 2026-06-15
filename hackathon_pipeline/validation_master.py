import json
import pandas as pd
import numpy as np
import lightgbm as lgb
from scipy.stats import spearmanr
from feature_extractor import extract_recruiter_features, FEATURE_COLS

print("Running Comprehensive Validation Phase...")

input_file = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
records = []
with open(input_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 10000: break
        if line.strip():
            try:
                records.append(json.loads(line))
            except:
                pass

df = pd.DataFrame(records)

print("Extracting features...")
features_df = extract_recruiter_features(df)
features_df['semantic_sim'] = np.random.uniform(0.3, 1.0, size=len(features_df))
features_df['bm25_score'] = np.random.uniform(0.0, 1.0, size=len(features_df))

model = lgb.Booster(model_file="lgbm_ranker_v2.txt")

# 1. PRODUCTION ML DOMINANCE AUDIT
print("\n=== 1. PRODUCTION ML DOMINANCE AUDIT ===")
prod_ml = features_df['production_ml_score']
print(f"Mean: {prod_ml.mean():.4f}")
print(f"Std: {prod_ml.std():.4f}")
print(f"Non-zero count: {(prod_ml > 0).sum()}")

# 2 & 3. MULTI-JD ROBUSTNESS & GENERALIZATION
print("\n=== 2 & 3. MULTI-JD ROBUSTNESS TEST ===")
jds = {
    'Search Engineer': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking'],
    'Frontend Engineer': ['react', 'vue', 'css', 'html', 'javascript', 'frontend'],
    'Sales Manager': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline']
}

for jd_name, jd_keywords in jds.items():
    print(f"\nEvaluating JD: {jd_name}")
    # Simulate Query alignment
    def jd_rel(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        ch = row.get('career_history', [])
        d_text = ch[0].get('description', '').lower() if ch else ''
        t_text = ch[0].get('title', '').lower() if ch else ''
        hits = sum(1 for k in jd_keywords if k in s_text or k in d_text or k in t_text)
        return min(hits / max(1, len(jd_keywords)), 1.0)
    
    df['jd_rel'] = df.apply(jd_rel, axis=1)
    
    # Overwrite dynamic query features
    features_df['semantic_sim'] = df['jd_rel'] * 0.8 + np.random.uniform(0, 0.2, size=len(df))
    features_df['bm25_score'] = df['jd_rel'] * 0.8 + np.random.uniform(0, 0.2, size=len(df))
    
    scores = model.predict(features_df[FEATURE_COLS])
    features_df['score'] = scores
    features_df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in df['career_history']]
    
    top_20 = features_df.nlargest(20, 'score')
    top_titles = top_20['current_title'].value_counts().head(3).to_dict()
    avg_auth = top_20['domain_authenticity_score'].mean()
    
    print(f"  Top 20 Titles: {top_titles}")
    print(f"  Avg Domain Authenticity: {avg_auth:.2f}")
    
    # Check generalisation ordering
    # Cohorts
    if jd_name == 'Sales Manager':
        rel_idx = features_df[features_df['current_title'].str.contains('sales')].index
        adj_idx = features_df[features_df['current_title'].str.contains('manager|executive')].index
    else:
        rel_idx = features_df[features_df['current_title'].str.contains(jd_name.split()[0].lower())].index
        adj_idx = features_df[features_df['current_title'].str.contains('engineer|developer')].index
        
    trap_idx = features_df[features_df['keyword_trap_risk'] > 0.5].index
    
    features_df['rank_pos'] = features_df['score'].rank(method='min', ascending=False)
    
    print(f"  Avg Rank - Relevant: {features_df.loc[rel_idx, 'rank_pos'].mean() if len(rel_idx)>0 else 'N/A'}")
    print(f"  Avg Rank - Adjacent: {features_df.loc[adj_idx, 'rank_pos'].mean() if len(adj_idx)>0 else 'N/A'}")
    print(f"  Avg Rank - Honeypot: {features_df.loc[trap_idx, 'rank_pos'].mean() if len(trap_idx)>0 else 'N/A'}")

print("\nValidation complete.")
