import json
import pandas as pd
import numpy as np

print("Running Title Monoculture Audit...")

# 1. LOAD DATASET
input_file = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
records = []
with open(input_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if line.strip():
            try:
                records.append(json.loads(line))
            except:
                pass

df = pd.DataFrame(records)
df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in df['career_history']]
df['current_company'] = [ch[0].get('company', '').lower() if ch else '' for ch in df['career_history']]

def get_skills(row):
    s_list = row.get('skills', []) or []
    return " ".join([s.get('name', '').lower() for s in s_list if isinstance(s, dict)])
df['skills_text'] = df.apply(get_skills, axis=1)

def calc_quality(c):
    s = c.get('redrob_signals', {})
    q = 0.0
    q += (s.get('profile_completeness_score', 50) / 100.0)
    q += min((s.get('github_activity_score', 0) / 100.0), 1.0)
    if s.get('verified_email'): q += 0.5
    if s.get('linkedin_connected'): q += 0.5
    return q
df['quality_score'] = df.apply(calc_quality, axis=1)

# JD Definitions
base_jds = {
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

title_removed_jds = {k: {**v, 'title_terms': []} for k, v in base_jds.items()}

title_synonym_jds = {
    'Search Engineer': {**base_jds['Search Engineer'], 'title_terms': ['information retrieval', 'relevance', 'search platform']},
    'Frontend Engineer': {**base_jds['Frontend Engineer'], 'title_terms': ['ui engineer', 'web engineer', 'client platform']},
    'Sales Manager': {**base_jds['Sales Manager'], 'title_terms': ['account executive lead', 'revenue operations']}
}

trap_titles = ['marketing', 'sales', 'hr', 'recruiter', 'manager', 'project manager', 'product manager', 'analyst', 'support', 'executive', 'director', 'accountant']

def extract_features(df_input, jd_data, is_sales=False):
    feat = df_input[['candidate_id', 'current_title', 'current_company', 'quality_score', 'skills_text', 'skills']].copy()
    
    def ext_features(row):
        s_text = row['skills_text']
        ch = df_input.loc[row.name, 'career_history']
        d_text = ch[0].get('description', '').lower() if ch else ''
        full = s_text + " " + d_text
        
        hits = sum(1 for k in jd_data['keywords'] if k in full)
        sem = hits / max(len(jd_data['keywords']), 1)
        bm25 = sem * 0.8
        
        t_text = row['current_title']
        t_hits = sum(1 for w in jd_data['title_terms'] if w in t_text)
        tsim = min(t_hits / 2.0, 1.0)
        
        sk_hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        scov = sk_hits / max(len(jd_data['req_skills']), 1)
        
        total_months = sum((job.get('duration_months', 0) or 0) for job in ch) if ch else 0
        yoe = total_months / 12.0
        diff = abs(yoe - jd_data['seniority_years'])
        sen = max(0, 1.0 - (diff / 10.0))
        
        trap = 1.0 if bm25 > 0.6 and tsim == 0 else 0.0
        return pd.Series([sem, bm25, tsim, scov, sen, trap])
        
    feat[['semantic_sim', 'bm25_score', 'title_similarity', 'skill_coverage', 'seniority_alignment', 'keyword_trap_penalty']] = feat.apply(ext_features, axis=1)
    
    feat['is_relevant'] = feat['current_title'].str.contains(jd_data['rel_regex'])
    if is_sales:
        feat['is_trap'] = feat['current_title'].str.contains('engineer|developer|scientist')
    else:
        feat['is_trap'] = feat['current_title'].apply(lambda t: any(tr in t for tr in trap_titles) and 'engineer' not in t)
    return feat

def rank_features(feat, w):
    feat['final_score'] = 0.0
    for k, weight in w.items():
        feat['final_score'] += feat[k] * weight
    return feat.sort_values(by='final_score', ascending=False)

# Original Weights
w_orig = {
    'title_similarity': 4.95,
    'semantic_sim': 2.18,
    'skill_coverage': 1.23,
    'seniority_alignment': 0.88,
    'quality_score': 0.81,
    'bm25_score': 0.62,
    'keyword_trap_penalty': -7.31
}

# 4. Weight Redistribution (More balanced, no single feature >40%)
# Reduce title to 2.5 (was 4.95). Increase Semantic to 3.5, BM25 to 2.5, Skill to 3.0.
# Keep Trap high to prevent honeypots.
w_new = {
    'title_similarity': 2.50,   # ~16%
    'semantic_sim': 3.50,       # ~23%
    'bm25_score': 2.50,         # ~16%
    'skill_coverage': 3.00,     # ~20%
    'seniority_alignment': 1.00,# ~6%
    'quality_score': 1.00,      # ~6%
    'keyword_trap_penalty': -8.00 
}

results = {}

for jd_name in base_jds.keys():
    print(f"\nProcessing {jd_name}...")
    is_sales = (jd_name == 'Sales Manager')
    
    # Extract
    feat_base = extract_features(df, base_jds[jd_name], is_sales)
    feat_rem = extract_features(df, title_removed_jds[jd_name], is_sales)
    feat_syn = extract_features(df, title_synonym_jds[jd_name], is_sales)
    
    # 1. Title Removal Stress Test
    ranked_rem = rank_features(feat_rem.copy(), w_orig)
    top100_rem = ranked_rem.head(100)
    
    # 2. Title Synonym Stress Test
    ranked_syn = rank_features(feat_syn.copy(), w_orig)
    top100_syn = ranked_syn.head(100)
    
    # 3. Percentiles + 4. Weight Redistribution
    ranked_orig = rank_features(feat_base.copy(), w_orig)
    ranked_new = rank_features(feat_base.copy(), w_new)
    
    all_rel_cnt = ranked_orig['is_relevant'].sum()
    total_pop = len(df)
    
    def get_metrics(ranked_df):
        top100 = ranked_df.head(100)
        rel_in_100 = top100['is_relevant'].sum()
        rec100 = rel_in_100 / all_rel_cnt if all_rel_cnt > 0 else 0
        trap_pen = (top100['is_trap'].sum() / 100) * 100
        avg_rank = ranked_df.reset_index(drop=True).index[ranked_df['is_relevant'].values].to_series().mean() + 1
        avg_pct = (avg_rank / total_pop) * 100
        return rec100, trap_pen, avg_pct

    rem_rec, rem_trap, rem_pct = get_metrics(ranked_rem)
    syn_rec, syn_trap, syn_pct = get_metrics(ranked_syn)
    orig_rec, orig_trap, orig_pct = get_metrics(ranked_orig)
    new_rec, new_trap, new_pct = get_metrics(ranked_new)
    
    # Overlap
    orig_ids = set(ranked_orig.head(100)['candidate_id'])
    syn_ids = set(top100_syn['candidate_id'])
    syn_overlap = len(orig_ids.intersection(syn_ids))
    
    results[jd_name] = {
        'total_relevant_population': int(all_rel_cnt),
        'title_removed': {'Recall@100': rem_rec, 'Honeypot%': rem_trap, 'Avg_Rank_Pct': rem_pct},
        'title_synonym': {'Recall@100': syn_rec, 'Honeypot%': syn_trap, 'Avg_Rank_Pct': syn_pct, 'Overlap_with_Orig': syn_overlap},
        'baseline': {'Recall@100': orig_rec, 'Honeypot%': orig_trap, 'Avg_Rank_Pct': orig_pct},
        'redistributed': {'Recall@100': new_rec, 'Honeypot%': new_trap, 'Avg_Rank_Pct': new_pct}
    }
    
    # 5. Top 100 Manual Review Export (Baseline vs Redistributed)
    def export_review(top100_df, filename):
        with open(filename, 'w') as f:
            for _, row in top100_df.iterrows():
                sk = []
                if isinstance(row['skills'], list):
                    for s in row['skills']:
                        if isinstance(s, dict) and s.get('name'): sk.append(s['name'].lower())
                f.write(f"Title: {row['current_title']} | Company: {row['current_company']} | Skills: {', '.join(sk[:5])}\n")
                
    export_review(ranked_orig.head(100), f"review_orig_{jd_name.replace(' ', '_')}.txt")
    export_review(ranked_new.head(100), f"review_new_{jd_name.replace(' ', '_')}.txt")

with open('title_monoculture_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nAudit Complete.")
