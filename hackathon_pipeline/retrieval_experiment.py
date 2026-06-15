import json
import pandas as pd
import numpy as np
import lightgbm as lgb
from feature_extractor import extract_recruiter_features, FEATURE_COLS

print("Running Ranking Experiment...")

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
features_df = extract_recruiter_features(df)
features_df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in df['career_history']]
model = lgb.Booster(model_file="lgbm_ranker_v2.txt")

jds = {
    'Search Engineer': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval'],
    'Frontend Engineer': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui'],
    'Sales Manager': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account']
}

for jd_name, jd_keywords in jds.items():
    print(f"\nEvaluating JD: {jd_name}")
    
    # Simulate robust semantic/bm25 query
    def jd_rel(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        ch = row.get('career_history', [])
        d_text = ch[0].get('description', '').lower() if ch else ''
        t_text = ch[0].get('title', '').lower() if ch else ''
        full = s_text + " " + d_text + " " + t_text
        hits = sum(1 for k in jd_keywords if k in full)
        # Add random noise for tie-breaking but ensure signal is strong
        return (hits / len(jd_keywords)) + np.random.uniform(0, 0.1)
    
    sim_scores = df.apply(jd_rel, axis=1)
    # Normalize to 0-1
    sim_scores = (sim_scores - sim_scores.min()) / (sim_scores.max() - sim_scores.min() + 1e-9)
    
    features_df['semantic_sim'] = sim_scores
    features_df['bm25_score'] = sim_scores

    # Define Method Scores
    # Method 1: Retrieval Only
    features_df['score_m1'] = features_df['semantic_sim'] + features_df['bm25_score']
    
    # Method 2: Current LightGBM
    features_df['score_m2'] = model.predict(features_df[FEATURE_COLS])
    
    # Method 3: Retrieval + Quality Only
    # normalize quality metrics slightly
    features_df['score_m3'] = (
        features_df['semantic_sim'] * 3.0 + 
        features_df['bm25_score'] * 2.0 + 
        features_df['leadership_score'] * 0.5 + 
        features_df['trust_score'] * 1.0 + 
        features_df['profile_completeness'] * 2.0 +
        features_df['hireability_score'] * 0.5
    )
    
    # Define Cohorts
    if jd_name == 'Sales Manager':
        rel_idx = features_df[features_df['current_title'].str.contains('sales')].index
        adj_idx = features_df[features_df['current_title'].str.contains('manager|executive|business') & ~features_df['current_title'].str.contains('sales')].index
    elif jd_name == 'Frontend Engineer':
        rel_idx = features_df[features_df['current_title'].str.contains('frontend|front-end|front end')].index
        adj_idx = features_df[features_df['current_title'].str.contains('software|developer|engineer') & ~features_df['current_title'].str.contains('frontend|front-end|front end')].index
    else: # Search Engineer
        rel_idx = features_df[features_df['current_title'].str.contains('search|ml|machine learning|ai')].index
        adj_idx = features_df[features_df['current_title'].str.contains('software|developer|engineer') & ~features_df['current_title'].str.contains('search|ml|machine learning|ai')].index
        
    trap_idx = features_df[features_df['keyword_trap_risk'] > 0.5].index

    methods = ['m1', 'm2', 'm3']
    method_names = ['Retrieval Only', 'LightGBM V2', 'Retrieval + Quality']
    
    for m, m_name in zip(methods, method_names):
        features_df[f'rank_{m}'] = features_df[f'score_{m}'].rank(method='min', ascending=False)
        rank_rel = features_df.loc[rel_idx, f'rank_{m}'].mean() if len(rel_idx)>0 else -1
        rank_adj = features_df.loc[adj_idx, f'rank_{m}'].mean() if len(adj_idx)>0 else -1
        rank_trap = features_df.loc[trap_idx, f'rank_{m}'].mean() if len(trap_idx)>0 else -1
        
        print(f"  [{m_name}] Avg Rank -> Relevant: {rank_rel:.1f} | Adjacent: {rank_adj:.1f} | Honeypot: {rank_trap:.1f}")

print("\nExperiment Complete.")
