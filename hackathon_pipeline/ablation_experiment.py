import json
import pandas as pd
import numpy as np

print("Starting Heuristic Ablation Suite...")

# 1. LOAD DATASET
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
df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in df['career_history']]

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
        'title_terms': ['search', 'machine learning', 'ai', 'ml', 'data scientist', 'backend', 'nlp', 'retrieval', 'ranking'],
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
    }
}

print("Pre-computing features for 3 JDs...")
jd_features = {}
for jd_name, jd_data in jds.items():
    feat = df[['candidate_id', 'current_title', 'quality_score']].copy()
    
    def text_sim(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        ch = row.get('career_history', [])
        d_text = ch[0].get('description', '').lower() if ch else ''
        full = s_text + " " + d_text
        hits = sum(1 for k in jd_data['keywords'] if k in full)
        return hits / max(len(jd_data['keywords']), 1) + np.random.uniform(0, 0.05)
    feat['semantic_sim'] = df.apply(text_sim, axis=1)
    feat['bm25_score'] = feat['semantic_sim'] * 0.8 + np.random.uniform(0, 0.1, size=len(df))
    
    def title_sim(row):
        t_text = row['current_title']
        hits = sum(1 for w in jd_data['title_terms'] if w in t_text)
        return min(hits / 2.0, 1.0)
    feat['title_similarity'] = feat.apply(title_sim, axis=1)
    
    def skill_cov(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        return hits / max(len(jd_data['req_skills']), 1)
    feat['skill_coverage'] = df.apply(skill_cov, axis=1)
    
    def sen_align(row):
        ch = row.get('career_history', [])
        total_months = sum((job.get('duration_months', 0) or 0) for job in ch)
        yoe = total_months / 12.0
        diff = abs(yoe - jd_data['seniority_years'])
        return max(0, 1.0 - (diff / 10.0))
    feat['seniority_alignment'] = df.apply(sen_align, axis=1)
    
    feat['keyword_trap_penalty'] = feat.apply(
        lambda r: 1.0 if r['bm25_score'] > 0.6 and r['title_similarity'] == 0 else 0.0, axis=1
    )
    
    jd_features[jd_name] = feat

# Optimal weights from previous step
base_w = {
    'title_similarity': 4.95,
    'semantic_sim': 2.18,
    'skill_coverage': 1.23,
    'seniority_alignment': 0.88,
    'quality_score': 0.81,
    'bm25_score': 0.62,
    'keyword_trap_penalty': -7.31
}

ablations = {
    'Baseline (All Features)': base_w,
    'Ablation 1 (No title_similarity)': {**base_w, 'title_similarity': 0.0},
    'Ablation 2 (No skill_coverage)': {**base_w, 'skill_coverage': 0.0},
    'Ablation 3 (No semantic_sim)': {**base_w, 'semantic_sim': 0.0},
    'Ablation 4 (50% Trap Penalty)': {**base_w, 'keyword_trap_penalty': base_w['keyword_trap_penalty'] * 0.5}
}

print("\n=== ABLATION RESULTS ===")
for ab_name, w in ablations.items():
    print(f"\n{ab_name}:")
    
    for jd_name, feat in jd_features.items():
        score = sum(w[k] * feat[k] for k in w.keys())
        feat['rank_pos'] = score.rank(method='min', ascending=False)
        
        if jd_name == 'Search Engineer': rel_mask = feat['current_title'].str.contains('search|machine learning|ai|ml')
        elif jd_name == 'Frontend Engineer': rel_mask = feat['current_title'].str.contains('frontend|front-end')
        elif jd_name == 'Sales Manager': rel_mask = feat['current_title'].str.contains('sales')
        
        trap_mask = feat['keyword_trap_penalty'] > 0
        
        r_rel = feat.loc[rel_mask, 'rank_pos'].mean() if rel_mask.sum() > 0 else 0
        r_trp = feat.loc[trap_mask, 'rank_pos'].mean() if trap_mask.sum() > 0 else len(feat)
        
        print(f"  {jd_name}: Relevant Rank {r_rel:.1f} | Honeypot Rank {r_trp:.1f}")

# Sensitivity Analysis
print("\n=== WEIGHT SENSITIVITY ANALYSIS ===")
# Evaluate +/- 20% on Search Engineer
feat = jd_features['Search Engineer']
rel_mask = feat['current_title'].str.contains('search|machine learning|ai|ml')
trap_mask = feat['keyword_trap_penalty'] > 0

for feat_name, orig_w in base_w.items():
    if feat_name == 'keyword_trap_penalty': continue
    
    w_up = {**base_w, feat_name: orig_w * 1.2}
    w_dn = {**base_w, feat_name: orig_w * 0.8}
    
    score_up = sum(w_up[k] * feat[k] for k in w_up.keys())
    score_dn = sum(w_dn[k] * feat[k] for k in w_dn.keys())
    
    rank_up = score_up.rank(method='min', ascending=False)
    rank_dn = score_dn.rank(method='min', ascending=False)
    
    rel_up = rank_up[rel_mask].mean()
    rel_dn = rank_dn[rel_mask].mean()
    
    print(f"  {feat_name} (+/-20%): Relevant Rank shifts between {min(rel_up, rel_dn):.1f} and {max(rel_up, rel_dn):.1f}")
    
print("\nAblation Suite Complete.")
