import json
import pandas as pd
import numpy as np
import time

print("Running JD-Relative Scoring Experiment...")

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
        'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval'],
        'title': 'search machine learning ai engineer',
        'req_skills': ['python', 'elasticsearch', 'faiss', 'machine learning'],
        'seniority_years': 5
    },
    'Frontend Engineer': {
        'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui'],
        'title': 'frontend front-end web developer engineer ui',
        'req_skills': ['javascript', 'react', 'css', 'html'],
        'seniority_years': 4
    },
    'Sales Manager': {
        'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account'],
        'title': 'sales manager account executive business development',
        'req_skills': ['sales', 'crm', 'b2b', 'negotiation'],
        'seniority_years': 6
    }
}

for jd_name, jd_data in jds.items():
    print(f"\nEvaluating JD: {jd_name}")
    start = time.time()
    
    # 1. Semantic & BM25 Proxy (Text overlap)
    def text_sim(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        ch = row.get('career_history', [])
        d_text = ch[0].get('description', '').lower() if ch else ''
        full = s_text + " " + d_text
        hits = sum(1 for k in jd_data['keywords'] if k in full)
        return hits / len(jd_data['keywords']) + np.random.uniform(0, 0.05)
    
    sim_scores = df.apply(text_sim, axis=1)
    df['semantic_sim'] = sim_scores
    df['bm25_score'] = sim_scores * 0.8 + np.random.uniform(0, 0.1, size=len(df))
    
    # 2. Required Skill Coverage
    def skill_cov(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        return hits / len(jd_data['req_skills'])
    df['required_skill_coverage'] = df.apply(skill_cov, axis=1)
    
    # 3. Title Similarity
    def title_sim(row):
        ch = row.get('career_history', [])
        t_text = ch[0].get('title', '').lower() if ch else ''
        jd_t = jd_data['title'].split()
        hits = sum(1 for w in jd_t if w in t_text)
        if len(t_text.split()) == 0: return 0.0
        return hits / max(1, min(len(jd_t), len(t_text.split())))
    df['title_similarity'] = df.apply(title_sim, axis=1)
    
    # 4. Seniority Alignment
    def sen_align(row):
        ch = row.get('career_history', [])
        total_months = sum((job.get('duration_months', 0) or 0) for job in ch)
        yoe = total_months / 12.0
        diff = abs(yoe - jd_data['seniority_years'])
        return max(0, 1.0 - (diff / 10.0))
    df['seniority_alignment'] = df.apply(sen_align, axis=1)
    
    # Weights
    w1, w2, w3, w4, w5, w6 = 2.0, 1.5, 3.0, 2.0, 1.0, 0.5
    
    df['final_score'] = (
        w1 * df['semantic_sim'] +
        w2 * df['bm25_score'] +
        w3 * df['required_skill_coverage'] +
        w4 * df['title_similarity'] +
        w5 * df['seniority_alignment'] +
        w6 * df['quality_score']
    )
    
    # Trap Penalty Proxy: Honeypots have high keyword hits but suspicious titles/experience logic
    # But in this model, honeypots won't easily fake title_similarity AND required_skill_coverage consistently 
    # without looking like the actual role! If they do, they are relevant.
    
    runtime = time.time() - start
    
    # Define Cohorts
    features_df = df.copy()
    features_df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in df['career_history']]
    features_df['keyword_trap_risk'] = features_df['current_title'].apply(lambda t: 1 if ('manager' in t or 'hr' in t or 'analyst' in t) and 'engineer' not in t else 0)
    
    if jd_name == 'Sales Manager':
        rel_idx = features_df[features_df['current_title'].str.contains('sales')].index
        adj_idx = features_df[features_df['current_title'].str.contains('marketing|executive|business') & ~features_df['current_title'].str.contains('sales')].index
    elif jd_name == 'Frontend Engineer':
        rel_idx = features_df[features_df['current_title'].str.contains('frontend|front-end|front end')].index
        adj_idx = features_df[features_df['current_title'].str.contains('software|developer|engineer') & ~features_df['current_title'].str.contains('frontend|front-end|front end')].index
    else: # Search Engineer
        rel_idx = features_df[features_df['current_title'].str.contains('search|ml|machine learning|ai')].index
        adj_idx = features_df[features_df['current_title'].str.contains('software|developer|engineer') & ~features_df['current_title'].str.contains('search|ml|machine learning|ai')].index
        
    trap_idx = features_df[(features_df['keyword_trap_risk'] > 0) & (features_df['semantic_sim'] > 0.5)].index
    
    features_df['rank_pos'] = features_df['final_score'].rank(method='min', ascending=False)
    rank_rel = features_df.loc[rel_idx, 'rank_pos'].mean() if len(rel_idx)>0 else -1
    rank_adj = features_df.loc[adj_idx, 'rank_pos'].mean() if len(adj_idx)>0 else -1
    rank_trap = features_df.loc[trap_idx, 'rank_pos'].mean() if len(trap_idx)>0 else -1
    
    print(f"  Runtime: {runtime:.4f}s")
    print(f"  Avg Rank -> Relevant: {rank_rel:.1f} | Adjacent: {rank_adj:.1f} | Honeypot: {rank_trap:.1f}")

print("\nJD-Relative Scoring Experiment Complete.")
