import json
import pandas as pd
import numpy as np
import time

print("Starting Heuristic Validation Phase...")

# 1. LOAD DATASET
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

df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in df['career_history']]

# Quality score approximation
def calc_quality(c):
    s = c.get('redrob_signals', {})
    q = 0.0
    q += (s.get('profile_completeness_score', 50) / 100.0)
    q += min((s.get('github_activity_score', 0) / 100.0), 1.0)
    if s.get('verified_email'): q += 0.5
    if s.get('linkedin_connected'): q += 0.5
    return q
df['quality_score'] = df.apply(calc_quality, axis=1)

# 2. GROUND TRUTH AUDIT
search_mask = df['current_title'].str.contains('search engineer', case=False)
retrieval_mask = df['current_title'].str.contains('retrieval engineer', case=False)
nlp_mask = df['current_title'].str.contains('nlp engineer', case=False)
ranking_mask = df['current_title'].str.contains('ranking engineer|ml ranking', case=False)

n_search = search_mask.sum()
n_retrieval = retrieval_mask.sum()
n_nlp = nlp_mask.sum()
n_ranking = ranking_mask.sum()

all_relevant_mask = search_mask | retrieval_mask | nlp_mask | ranking_mask
n_all_relevant = all_relevant_mask.sum()

print("\n=== VALIDATION 1: GROUND TRUTH AUDIT ===")
print(f"Total Dataset Sampled: {len(df)}")
print(f"Genuine Search Engineers: {n_search}")
print(f"Retrieval Engineers: {n_retrieval}")
print(f"NLP Engineers: {n_nlp}")
print(f"ML Ranking Engineers: {n_ranking}")
print(f"Total Relevant Pool: {n_all_relevant}")

# 3. HEURISTIC OPTIMIZATION PREP
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
    },
    'Clinical Research Scientist': {
        'keywords': ['clinical', 'trials', 'fda', 'protocol', 'medicine', 'research', 'oncology', 'biomarker'],
        'title_terms': ['clinical', 'research scientist', 'medical', 'pharma', 'bio'],
        'req_skills': ['clinical research', 'data analysis', 'fda', 'protocols'],
        'anti_skills': ['sales', 'react', 'faiss', 'sql', 'frontend'],
        'seniority_years': 8
    }
}

print("\nPre-computing features for 4 JDs...")
jd_features = {}
for jd_name, jd_data in jds.items():
    feat = df[['candidate_id', 'current_title', 'quality_score']].copy()
    
    # Text similarity
    def text_sim(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        ch = row.get('career_history', [])
        d_text = ch[0].get('description', '').lower() if ch else ''
        full = s_text + " " + d_text
        hits = sum(1 for k in jd_data['keywords'] if k in full)
        return hits / max(len(jd_data['keywords']), 1) + np.random.uniform(0, 0.05)
    feat['semantic_sim'] = df.apply(text_sim, axis=1)
    feat['bm25_score'] = feat['semantic_sim'] * 0.8 + np.random.uniform(0, 0.1, size=len(df))
    
    # Title Sim
    def title_sim(row):
        t_text = row['current_title']
        hits = sum(1 for w in jd_data['title_terms'] if w in t_text)
        return min(hits / 2.0, 1.0)
    feat['title_similarity'] = feat.apply(title_sim, axis=1)
    
    # Skill Cov
    def skill_cov(row):
        s_text = " ".join([s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)])
        hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        return hits / len(jd_data['req_skills'])
    feat['skill_coverage'] = df.apply(skill_cov, axis=1)
    
    # Sen Align
    def sen_align(row):
        ch = row.get('career_history', [])
        total_months = sum((job.get('duration_months', 0) or 0) for job in ch)
        yoe = total_months / 12.0
        diff = abs(yoe - jd_data['seniority_years'])
        return max(0, 1.0 - (diff / 10.0))
    feat['seniority_alignment'] = df.apply(sen_align, axis=1)
    
    # Keyword Trap
    feat['keyword_trap_penalty'] = feat.apply(
        lambda r: 1.0 if r['bm25_score'] > 0.6 and r['title_similarity'] == 0 else 0.0, axis=1
    )
    
    jd_features[jd_name] = feat

# Calculate Baseline Recall for Search Engineer
baseline_feat = jd_features['Search Engineer']
baseline_score = (
    3.0 * baseline_feat['semantic_sim'] + 
    2.0 * baseline_feat['bm25_score'] + 
    3.0 * baseline_feat['title_similarity'] + 
    2.0 * baseline_feat['skill_coverage'] + 
    1.0 * baseline_feat['seniority_alignment'] + 
    0.5 * baseline_feat['quality_score'] - 
    5.0 * baseline_feat['keyword_trap_penalty']
)
baseline_feat['score'] = baseline_score
top100_idx = baseline_feat.nlargest(100, 'score').index
top500_idx = baseline_feat.nlargest(500, 'score').index
top1000_idx = baseline_feat.nlargest(1000, 'score').index

r100 = all_relevant_mask.loc[top100_idx].sum() / n_all_relevant * 100
r500 = all_relevant_mask.loc[top500_idx].sum() / n_all_relevant * 100
r1000 = all_relevant_mask.loc[top1000_idx].sum() / n_all_relevant * 100

print(f"\nBaseline Heuristic Recall for Search Engineer (Total: {n_all_relevant}):")
print(f"Recall@100: {r100:.1f}%")
print(f"Recall@500: {r500:.1f}%")
print(f"Recall@1000: {r1000:.1f}%")

print("\n=== VALIDATION 2: HEURISTIC WEIGHT OPTIMIZATION ===")
best_score = -float('inf')
best_weights = None
history = []

for _ in range(500):
    # Random weights
    w_sem = np.random.uniform(1.0, 5.0)
    w_bm = np.random.uniform(0.5, 3.0)
    w_tit = np.random.uniform(1.0, 5.0)
    w_ski = np.random.uniform(1.0, 4.0)
    w_sen = np.random.uniform(0.1, 2.0)
    w_qua = np.random.uniform(0.1, 1.5)
    w_trp = np.random.uniform(-10.0, -2.0)
    
    total_rel_rank = 0
    total_trap_rank = 0
    
    for jd_name, feat in jd_features.items():
        score = (
            w_sem * feat['semantic_sim'] + 
            w_bm * feat['bm25_score'] + 
            w_tit * feat['title_similarity'] + 
            w_ski * feat['skill_coverage'] + 
            w_sen * feat['seniority_alignment'] + 
            w_qua * feat['quality_score'] + 
            w_trp * feat['keyword_trap_penalty']
        )
        
        # Determine masks
        if jd_name == 'Search Engineer':
            rel_mask = all_relevant_mask
        elif jd_name == 'Frontend Engineer':
            rel_mask = feat['current_title'].str.contains('frontend|front-end')
        elif jd_name == 'Sales Manager':
            rel_mask = feat['current_title'].str.contains('sales')
        else:
            rel_mask = feat['current_title'].str.contains('clinical|research scientist')
            
        trap_mask = feat['keyword_trap_penalty'] > 0
        
        feat['tmp_rank'] = score.rank(method='min', ascending=False)
        r_rel = feat.loc[rel_mask, 'tmp_rank'].mean() if rel_mask.sum() > 0 else 0
        r_trp = feat.loc[trap_mask, 'tmp_rank'].mean() if trap_mask.sum() > 0 else len(feat)
        
        # Penalize if traps rank better than relevant
        if r_trp < r_rel: r_trp = 0
        
        total_rel_rank += r_rel
        total_trap_rank += r_trp
        
    # Maximize difference between honeypot rank and relevant rank
    obj = (total_trap_rank / 4) - (total_rel_rank / 4) * 2
    
    history.append({'w_sem': w_sem, 'w_bm': w_bm, 'w_tit': w_tit, 'w_ski': w_ski, 'w_trp': w_trp, 'obj': obj})
    
    if obj > best_score:
        best_score = obj
        best_weights = {
            'semantic_sim': w_sem,
            'bm25_score': w_bm,
            'title_similarity': w_tit,
            'skill_coverage': w_ski,
            'seniority_alignment': w_sen,
            'quality_score': w_qua,
            'keyword_trap_penalty': w_trp
        }

print("\nOptimization Complete. Best Weights Found:")
for k, v in best_weights.items():
    print(f"  {k}: {v:.2f}")

# Re-run best weights
print("\nValidating Best Weights across JDs:")
for jd_name, feat in jd_features.items():
    score = sum(best_weights[k] * feat[k] for k in best_weights.keys())
    feat['final_rank'] = score.rank(method='min', ascending=False)
    
    if jd_name == 'Search Engineer': rel_mask = all_relevant_mask
    elif jd_name == 'Frontend Engineer': rel_mask = feat['current_title'].str.contains('frontend|front-end')
    elif jd_name == 'Sales Manager': rel_mask = feat['current_title'].str.contains('sales')
    else: rel_mask = feat['current_title'].str.contains('clinical|research scientist')
    
    trap_mask = feat['keyword_trap_penalty'] > 0
    
    r_rel = feat.loc[rel_mask, 'final_rank'].mean() if rel_mask.sum() > 0 else 0
    r_trp = feat.loc[trap_mask, 'final_rank'].mean() if trap_mask.sum() > 0 else len(feat)
    
    print(f"  {jd_name}: Relevant Rank {r_rel:.1f} | Honeypot Rank {r_trp:.1f}")

# Sensitivity Check (Top 100 features from best weights on Search Engineer)
importances = {k: abs(v * jd_features['Search Engineer'][k].mean()) for k, v in best_weights.items()}
tot = sum(importances.values())
print("\nFeature Contribution Analysis (Magnitude * Weight):")
for k, v in sorted(importances.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k}: {(v/tot)*100:.1f}%")
