import json
import pandas as pd
import numpy as np
import math
from collections import Counter

print("Generating Ranking Truth Data...")

# 1. LOAD DATASET
input_file = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
records = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                records.append(json.loads(line))
            except:
                pass

df = pd.DataFrame(records)
df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in df['career_history']]
df['current_company'] = [ch[0].get('company', '').lower() if ch else '' for ch in df['career_history']]

# Clinical Research Audit
clin_mask = df['current_title'].str.contains('clinical research', case=False)
clin_df = df[clin_mask]
clin_data = {
    'count': len(clin_df),
    'candidates': [{'id': row['candidate_id'], 'title': row['current_title']} for _, row in clin_df.iterrows()]
}
with open('clin_truth.json', 'w') as f:
    json.dump(clin_data, f)

# Feature extraction logic
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
        'seniority_years': 5,
        'rel_regex': 'search engineer|retrieval engineer|nlp engineer|ranking engineer|ml ranking|ai research engineer|machine learning engineer'
    },
    'Frontend Engineer': {
        'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui', 'typescript'],
        'title_terms': ['frontend', 'front-end', 'web', 'ui', 'javascript'],
        'req_skills': ['javascript', 'react', 'css', 'html'],
        'seniority_years': 4,
        'rel_regex': 'frontend|front-end|web developer|ui developer'
    },
    'Sales Manager': {
        'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
        'title_terms': ['sales', 'account executive', 'business development', 'growth'],
        'req_skills': ['sales', 'crm', 'b2b', 'negotiation'],
        'seniority_years': 6,
        'rel_regex': 'sales|account executive|business development'
    }
}

weights = {
    'title_similarity': 4.95,
    'semantic_sim': 2.18,
    'skill_coverage': 1.23,
    'seniority_alignment': 0.88,
    'quality_score': 0.81,
    'bm25_score': 0.62,
    'keyword_trap_penalty': -7.31
}

# Trap definition
trap_titles = ['marketing', 'sales', 'hr', 'recruiter', 'manager', 'project manager', 'product manager', 'analyst', 'support', 'executive', 'director', 'accountant']

results = {}

for jd_name, jd_data in jds.items():
    print(f"Processing {jd_name}...")
    feat = df[['candidate_id', 'current_title', 'current_company', 'quality_score', 'skills']].copy()
    
    def ext_features(row):
        s_list = row.get('skills', []) or []
        s_text = " ".join([s.get('name', '').lower() for s in s_list if isinstance(s, dict)])
        ch = df.loc[row.name, 'career_history']
        d_text = ch[0].get('description', '').lower() if ch else ''
        full = s_text + " " + d_text
        
        # semantic/bm25
        hits = sum(1 for k in jd_data['keywords'] if k in full)
        sem = hits / max(len(jd_data['keywords']), 1)
        bm25 = sem * 0.8
        
        # title
        t_text = row['current_title']
        t_hits = sum(1 for w in jd_data['title_terms'] if w in t_text)
        tsim = min(t_hits / 2.0, 1.0)
        
        # skills
        sk_hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        scov = sk_hits / max(len(jd_data['req_skills']), 1)
        
        # sen
        total_months = sum((job.get('duration_months', 0) or 0) for job in ch) if ch else 0
        yoe = total_months / 12.0
        diff = abs(yoe - jd_data['seniority_years'])
        sen = max(0, 1.0 - (diff / 10.0))
        
        trap = 1.0 if bm25 > 0.6 and tsim == 0 else 0.0
        
        return pd.Series([sem, bm25, tsim, scov, sen, trap])
        
    feat[['semantic_sim', 'bm25_score', 'title_similarity', 'skill_coverage', 'seniority_alignment', 'keyword_trap_penalty']] = feat.apply(ext_features, axis=1)
    
    # Calculate score
    feat['final_score'] = 0.0
    for k, w in weights.items():
        feat['final_score'] += feat[k] * w
        
    # Is Relevant & Is Trap
    feat['is_relevant'] = feat['current_title'].str.contains(jd_data['rel_regex'])
    # For Sales, 'sales' is a trap if looking for Engineer, but here we adjust trap def dynamically:
    if jd_name == 'Sales Manager':
        is_trap = feat['current_title'].str.contains('engineer|developer|scientist')
    else:
        is_trap = feat['current_title'].apply(lambda t: any(tr in t for tr in trap_titles) and 'engineer' not in t)
    feat['is_trap'] = is_trap
        
    # Top 100 base
    feat_sorted = feat.sort_values(by='final_score', ascending=False)
    top100 = feat_sorted.head(100).copy()
    
    # Entropy
    def calc_entropy(counts):
        total = sum(counts)
        return -sum((c/total)*math.log2(c/total) for c in counts if c > 0)
        
    title_ent = calc_entropy(top100['current_title'].value_counts().values)
    comp_ent = calc_entropy(top100['current_company'].value_counts().values)
    
    sk_list = []
    for s_arr in top100['skills']:
        if isinstance(s_arr, list):
            for s in s_arr:
                if isinstance(s, dict) and s.get('name'): sk_list.append(s['name'].lower())
    sk_ent = calc_entropy(list(Counter(sk_list).values()))
    
    # Extract contributions
    top100_contribs = []
    for _, row in top100.iterrows():
        top100_contribs.append({
            'candidate_id': row['candidate_id'],
            'title': row['current_title'],
            'final_score': row['final_score'],
            'title_similarity_contrib': row['title_similarity'] * weights['title_similarity'],
            'semantic_sim_contrib': row['semantic_sim'] * weights['semantic_sim'],
            'bm25_contrib': row['bm25_score'] * weights['bm25_score'],
            'skill_coverage_contrib': row['skill_coverage'] * weights['skill_coverage'],
            'seniority_contrib': row['seniority_alignment'] * weights['seniority_alignment'],
            'quality_contrib': row['quality_score'] * weights['quality_score'],
            'trap_penalty_contrib': row['keyword_trap_penalty'] * weights['keyword_trap_penalty']
        })
        
    # Ablations
    abl_results = {}
    for ab_feat in weights.keys():
        ab_w = weights.copy()
        ab_w[ab_feat] = 0.0
        
        ab_scores = pd.Series(0.0, index=feat.index)
        for k, w in ab_w.items():
            ab_scores += feat[k] * w
            
        r_pos = ab_scores.rank(method='min', ascending=False)
        
        # Top 100
        top100_idx = ab_scores.nlargest(100).index
        top100_trap = feat.loc[top100_idx, 'is_trap'].sum()
        
        # Metrics
        all_rel_cnt = feat['is_relevant'].sum()
        rel_in_top100 = feat.loc[top100_idx, 'is_relevant'].sum()
        rec100 = rel_in_top100 / all_rel_cnt if all_rel_cnt > 0 else 0
        avg_rel_rank = r_pos[feat['is_relevant']].mean() if all_rel_cnt > 0 else 0
        
        abl_results[ab_feat] = {
            'Recall@100': rec100,
            'Honeypot Penetration %': (top100_trap/100)*100,
            'Avg Relevant Rank': avg_rel_rank
        }
        
    # Base metrics
    all_rel_cnt = feat['is_relevant'].sum()
    rec100 = feat.loc[top100.index, 'is_relevant'].sum() / all_rel_cnt if all_rel_cnt > 0 else 0
    rel_ranks = feat_sorted.reset_index(drop=True).index[feat_sorted['is_relevant'].values]
    avg_rel_rank = pd.Series(rel_ranks).mean() + 1 if len(rel_ranks) > 0 else 0
    
    results[jd_name] = {
        'base_metrics': {
            'Recall@100': rec100,
            'Honeypot Penetration %': (top100['is_trap'].sum() / 100) * 100,
            'Avg Relevant Rank': avg_rel_rank
        },
        'entropy': {
            'title': title_ent,
            'company': comp_ent,
            'skill': sk_ent
        },
        'ablations': abl_results,
        'top_contribs': top100_contribs[:3]  # Just save a sample to json, report will summarize
    }
    
    df_contribs = pd.DataFrame(top100_contribs)
    df_contribs.to_csv(f"top100_contribs_{jd_name.replace(' ', '_')}.csv", index=False)

with open('ranking_truth_results.json', 'w') as f:
    json.dump(results, f)

print("Done.")
