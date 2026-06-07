import json
import pandas as pd
import numpy as np
import lightgbm as lgb
import time

print("Building Complete JD-Relative Feature Space and Running System Comparison...")

input_file = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
records = []
with open(input_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 10000: break # Subset for fast experiment
        if line.strip():
            try:
                records.append(json.loads(line))
            except:
                pass

df = pd.DataFrame(records)

# Approximate candidate quality baseline quickly
def calc_quality(c):
    s = c.get('redrob_signals', {})
    q = 0.0
    q += (s.get('profile_completeness_score', 50) / 100.0)
    q += min((s.get('github_activity_score', 0) / 100.0), 1.0)
    if s.get('verified_email'): q += 0.5
    if s.get('linkedin_connected'): q += 0.5
    return q

df['quality_score'] = df.apply(calc_quality, axis=1)

jds = {
    'Search Engineer': {
        'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
        'title_terms': ['search', 'machine learning', 'ai', 'ml', 'data scientist', 'backend'],
        'req_skills': ['python', 'elasticsearch', 'faiss', 'machine learning'],
        'anti_skills': ['sales', 'hr', 'recruiter', 'accountant'],
        'seniority_years': 5
    },
    'Frontend Engineer': {
        'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui', 'typescript'],
        'title_terms': ['frontend', 'front-end', 'web', 'ui', 'javascript'],
        'req_skills': ['javascript', 'react', 'css', 'html'],
        'anti_skills': ['sales', 'machine learning', 'faiss', 'hr'],
        'seniority_years': 4
    },
    'Sales Manager': {
        'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
        'title_terms': ['sales', 'account executive', 'business development', 'growth'],
        'req_skills': ['sales', 'crm', 'b2b', 'negotiation'],
        'anti_skills': ['python', 'react', 'engineer', 'developer', 'machine learning'],
        'seniority_years': 6
    },
    'Clinical Research Scientist': {
        'keywords': ['clinical', 'trials', 'fda', 'protocol', 'medicine', 'research', 'oncology', 'biomarker'],
        'title_terms': ['clinical', 'research scientist', 'medical', 'pharma', 'bio'],
        'req_skills': ['clinical research', 'data analysis', 'fda', 'protocols'],
        'anti_skills': ['sales', 'react', 'faiss', 'sql', 'frontend'],
        'seniority_years': 8
    }
}

feature_cols = [
    'semantic_sim', 'bm25_score', 'title_similarity', 
    'skill_coverage', 'seniority_alignment', 'anti_skill_penalty', 
    'keyword_stuffing_risk', 'quality_score'
]

# Generate unified dataset for LightGBM
all_features = []
all_labels = []

print("Extracting features for all JDs...")
start_extract = time.time()
jd_dfs = {}

for jd_name, jd_data in jds.items():
    jd_df = df.copy()
    
    # 1. Semantic & BM25 Proxy (Text overlap + noise to break ties)
    def text_sim(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        ch = row.get('career_history', [])
        d_text = ch[0].get('description', '').lower() if ch else ''
        full = s_text + " " + d_text
        hits = sum(1 for k in jd_data['keywords'] if k in full)
        return hits / max(len(jd_data['keywords']), 1) + np.random.uniform(0, 0.05)
    
    sim_scores = jd_df.apply(text_sim, axis=1)
    jd_df['semantic_sim'] = sim_scores
    jd_df['bm25_score'] = sim_scores * 0.8 + np.random.uniform(0, 0.1, size=len(jd_df))
    
    # 2. Required Skill Coverage
    def skill_cov(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        return hits / len(jd_data['req_skills'])
    jd_df['skill_coverage'] = jd_df.apply(skill_cov, axis=1)
    
    # 3. Title Similarity
    def title_sim(row):
        ch = row.get('career_history', [])
        t_text = ch[0].get('title', '').lower() if ch else ''
        hits = sum(1 for w in jd_data['title_terms'] if w in t_text)
        return min(hits / 2.0, 1.0)
    jd_df['title_similarity'] = jd_df.apply(title_sim, axis=1)
    
    # 4. Seniority Alignment
    def sen_align(row):
        ch = row.get('career_history', [])
        total_months = sum((job.get('duration_months', 0) or 0) for job in ch)
        yoe = total_months / 12.0
        diff = abs(yoe - jd_data['seniority_years'])
        return max(0, 1.0 - (diff / 10.0))
    jd_df['seniority_alignment'] = jd_df.apply(sen_align, axis=1)
    
    # 5. Anti-Skill Penalty
    def anti_skill(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        ch = row.get('career_history', [])
        t_text = ch[0].get('title', '').lower() if ch else ''
        full = s_text + " " + t_text
        hits = sum(1 for k in jd_data['anti_skills'] if k in full)
        return min(hits / 2.0, 1.0)
    jd_df['anti_skill_penalty'] = jd_df.apply(anti_skill, axis=1)
    
    # 6. Keyword Stuffing Risk
    # High BM25 but Zero title similarity AND zero quality
    jd_df['keyword_stuffing_risk'] = jd_df.apply(
        lambda r: 1.0 if r['bm25_score'] > 0.6 and r['title_similarity'] == 0 else 0.0, axis=1
    )
    
    # Generate Pseudo-Label using strict heuristic
    # This acts as our "ground truth" for what a perfect hire looks like
    h_score = (
        3.0 * jd_df['semantic_sim'] + 
        2.0 * jd_df['bm25_score'] + 
        3.0 * jd_df['title_similarity'] + 
        2.0 * jd_df['skill_coverage'] + 
        1.0 * jd_df['seniority_alignment'] + 
        0.5 * jd_df['quality_score'] - 
        3.0 * jd_df['anti_skill_penalty'] - 
        3.0 * jd_df['keyword_stuffing_risk']
    )
    
    # Bucket into LambdaRank classes (1 to 4)
    q33 = np.percentile(h_score, 60)
    q66 = np.percentile(h_score, 85)
    q90 = np.percentile(h_score, 98)
    
    def to_label(val):
        if val >= q90: return 4
        if val >= q66: return 3
        if val >= q33: return 2
        return 1
        
    labels = h_score.apply(to_label).values
    
    # Store for global training
    all_features.append(jd_df[feature_cols])
    all_labels.extend(labels)
    
    # Save df for later evaluation
    jd_df['heuristic_score'] = h_score
    jd_df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in jd_df['career_history']]
    jd_dfs[jd_name] = jd_df

print(f"Extraction complete in {time.time()-start_extract:.2f}s")

# Combine all datasets to train System C (Global LightGBM)
X_train = pd.concat(all_features, ignore_index=True)
y_train = np.array(all_labels)

# Grouping
group = [len(df)] * len(jds)

print("Training System C (Global LightGBM)...")
train_data = lgb.Dataset(X_train, label=y_train, group=group)
params = {
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'ndcg_eval_at': [10, 20],
    'learning_rate': 0.05,
    'num_leaves': 31,
    'min_data_in_leaf': 20,
    'verbose': -1
}

lgb_model = lgb.train(params, train_data, num_boost_round=100)

# Evaluate Feature Importance
importance = lgb_model.feature_importance(importance_type='gain')
total_gain = sum(importance)
gain_dict = {name: (imp / total_gain * 100) for name, imp in zip(feature_cols, importance) if total_gain > 0}
gain_dict = dict(sorted(gain_dict.items(), key=lambda x: x[1], reverse=True))

print("\n=== SYSTEM C FEATURE GAIN IMPORTANCE ===")
for k, v in gain_dict.items():
    print(f"{k}: {v:.1f}%")

print("\n=== EVALUATION ACROSS JDs ===")
report = ""

for jd_name, jd_df in jd_dfs.items():
    print(f"\\nEvaluating {jd_name}...")
    
    # System A: Retrieval Only
    jd_df['sys_a'] = jd_df['semantic_sim'] + jd_df['bm25_score']
    
    # System B: Heuristic (Already computed as heuristic_score)
    jd_df['sys_b'] = jd_df['heuristic_score']
    
    # System C: LightGBM
    jd_df['sys_c'] = lgb_model.predict(jd_df[feature_cols])
    
    # Evaluate Cohorts
    if jd_name == 'Sales Manager':
        rel_idx = jd_df[jd_df['current_title'].str.contains('sales')].index
        adj_idx = jd_df[jd_df['current_title'].str.contains('manager|executive|business') & ~jd_df['current_title'].str.contains('sales')].index
    elif jd_name == 'Frontend Engineer':
        rel_idx = jd_df[jd_df['current_title'].str.contains('frontend|front-end|front end')].index
        adj_idx = jd_df[jd_df['current_title'].str.contains('software|developer|engineer') & ~jd_df['current_title'].str.contains('frontend|front-end|front end')].index
    elif jd_name == 'Clinical Research Scientist':
        rel_idx = jd_df[jd_df['current_title'].str.contains('clinical|research scientist|medical')].index
        adj_idx = jd_df[jd_df['current_title'].str.contains('scientist|research') & ~jd_df['current_title'].str.contains('clinical|medical')].index
    else: # Search Engineer
        rel_idx = jd_df[jd_df['current_title'].str.contains('search|machine learning|ai|ml')].index
        adj_idx = jd_df[jd_df['current_title'].str.contains('software|developer|engineer') & ~jd_df['current_title'].str.contains('search|machine learning|ai|ml')].index
        
    # Honeypot definition (For this specific dataset, honeypots are mostly fake search engineers)
    trap_idx = jd_df[(jd_df['keyword_stuffing_risk'] > 0)].index
    
    systems = {'System A (Retrieval)': 'sys_a', 'System B (Heuristic)': 'sys_b', 'System C (LightGBM)': 'sys_c'}
    
    for sys_name, col_name in systems.items():
        jd_df[f'rank_{col_name}'] = jd_df[col_name].rank(method='min', ascending=False)
        rank_rel = jd_df.loc[rel_idx, f'rank_{col_name}'].mean() if len(rel_idx)>0 else -1
        rank_adj = jd_df.loc[adj_idx, f'rank_{col_name}'].mean() if len(adj_idx)>0 else -1
        rank_trap = jd_df.loc[trap_idx, f'rank_{col_name}'].mean() if len(trap_idx)>0 else -1
        
        top_20 = jd_df.nlargest(20, col_name)
        top_titles = top_20['current_title'].value_counts().head(3).to_dict()
        
        print(f"  [{sys_name}]")
        print(f"    Avg Rank -> Relevant: {rank_rel:.1f} | Adjacent: {rank_adj:.1f} | Honeypot: {rank_trap:.1f}")
        print(f"    Top Titles: {top_titles}")

print("\nExperiment Complete.")
