import json
import pandas as pd
import numpy as np
import os
import time

print("Creating Phase 0 Archival Checkpoint...")

archive_dir = "archive_v1_frozen"
os.makedirs(archive_dir, exist_ok=True)

# 1. Ranking Logic Configuration
config = {
    "weights": {
        'title_affinity': 2.50,
        'skill_affinity': 3.50,
        'career_affinity': 2.50,
        'semantic_sim': 1.00,
        'bm25_score': 1.00,
        'quality_score': 1.00,
        'consistency_penalty': -2.00
    },
    "role_families": {
        'Search Engineer': ['search', 'retrieval', 'relevance', 'ranking', 'nlp', 'machine learning', 'ai', 'data scientist', 'ml'],
        'Frontend Engineer': ['frontend', 'ui', 'ux', 'client', 'web', 'javascript', 'react', 'angular', 'vue', 'front-end'],
        'Sales Manager': ['sales', 'revenue', 'account', 'business development', 'gtm', 'growth', 'customer success', 'marketing', 'manager', 'executive']
    },
    "skill_families": {
        'Search Engineer': ['python', 'elasticsearch', 'faiss', 'machine learning', 'nlp', 'deep learning', 'pytorch', 'tensorflow', 'scikit-learn'],
        'Frontend Engineer': ['javascript', 'react', 'css', 'html', 'typescript', 'ui/ux', 'vue', 'angular', 'redux', 'next.js'],
        'Sales Manager': ['sales', 'crm', 'b2b', 'negotiation', 'leadership', 'pipeline', 'salesforce', 'marketing', 'quota']
    },
    "trap_titles": ['marketing', 'sales', 'hr', 'recruiter', 'manager', 'project manager', 'product manager', 'analyst', 'support', 'executive', 'director', 'accountant']
}

with open(os.path.join(archive_dir, 'config_v1.json'), 'w') as f:
    json.dump(config, f, indent=2)

base_jds = {
    'Search Engineer': {
        'family': 'Search Engineer',
        'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
        'title_terms': config['role_families']['Search Engineer'],
        'req_skills': config['skill_families']['Search Engineer']
    },
    'Frontend Engineer': {
        'family': 'Frontend Engineer',
        'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui', 'typescript'],
        'title_terms': config['role_families']['Frontend Engineer'],
        'req_skills': config['skill_families']['Frontend Engineer']
    },
    'Sales Manager': {
        'family': 'Sales Manager',
        'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
        'title_terms': config['role_families']['Sales Manager'],
        'req_skills': config['skill_families']['Sales Manager']
    }
}

# 2. Dataset Loading
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

def get_skills(row):
    s_list = row.get('skills', []) or []
    return " ".join([s.get('name', '').lower() for s in s_list if isinstance(s, dict)])
df['skills_text'] = df.apply(get_skills, axis=1)

def get_desc(row):
    ch = row.get('career_history', [])
    return " ".join([c.get('description', '').lower() for c in ch if isinstance(c, dict)])
df['desc_text'] = df.apply(get_desc, axis=1)

def calc_quality(c):
    s = c.get('redrob_signals', {})
    q = 0.0
    q += (s.get('profile_completeness_score', 50) / 100.0)
    q += min((s.get('github_activity_score', 0) / 100.0), 1.0)
    if s.get('verified_email'): q += 0.5
    if s.get('linkedin_connected'): q += 0.5
    return q
df['quality_score'] = df.apply(calc_quality, axis=1)

def extract_features(df_input, jd_data):
    feat = df_input[['candidate_id', 'current_title', 'quality_score', 'skills_text', 'skills', 'desc_text']].copy()
    jd_fam = jd_data['family']
    
    def ext_features(row):
        s_text = row['skills_text']
        d_text = row['desc_text']
        t_text = row['current_title']
        full = s_text + " " + d_text
        
        t_hits = sum(1 for w in jd_data['title_terms'] if w in t_text)
        taff = min(t_hits / 2.0, 1.0)
        
        sk_hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        saff = sk_hits / max(len(jd_data['req_skills']), 1)
        
        c_hits = sum(1 for k in jd_data['keywords'] if k in d_text)
        caff = c_hits / max(len(jd_data['keywords']), 1)
        
        hits = sum(1 for k in jd_data['keywords'] if k in full)
        sem = hits / max(len(jd_data['keywords']), 1)
        bm25 = sem * 0.8
        
        cand_t_fam = max([(fam, sum(1 for w in terms if w in t_text)) for fam, terms in config['role_families'].items()], key=lambda x: x[1])
        cand_s_fam = max([(fam, sum(1 for k in terms if k in s_text)) for fam, terms in config['skill_families'].items()], key=lambda x: x[1])
        cand_c_fam = max([(fam, sum(1 for k in terms if k in d_text)) for fam, terms in config['skill_families'].items()], key=lambda x: x[1])
        
        t_fam = cand_t_fam[0] if cand_t_fam[1] > 0 else 'Unknown'
        s_fam = cand_s_fam[0] if cand_s_fam[1] > 0 else 'Unknown'
        c_fam = cand_c_fam[0] if cand_c_fam[1] > 0 else 'Unknown'
        
        is_consistent = (t_fam == jd_fam) and (s_fam == jd_fam) and (c_fam == jd_fam)
        is_inconsistent = (t_fam != jd_fam and t_fam != 'Unknown') and (s_fam != jd_fam and s_fam != 'Unknown') and (c_fam != jd_fam and c_fam != 'Unknown')
        is_partial = not is_consistent and not is_inconsistent
        
        return pd.Series([sem, bm25, taff, saff, caff, t_fam, s_fam, c_fam, is_consistent, is_inconsistent, is_partial])
        
    feat[['semantic_sim', 'bm25_score', 'title_affinity', 'skill_affinity', 'career_affinity', 't_fam', 's_fam', 'c_fam', 'is_consistent', 'is_inconsistent', 'is_partial']] = feat.apply(ext_features, axis=1)
    
    is_sales = (jd_fam == 'Sales Manager')
    if is_sales:
        feat['is_trap'] = feat['current_title'].str.contains('engineer|developer|scientist|data')
    else:
        feat['is_trap'] = feat['current_title'].apply(lambda t: any(tr in t for tr in config['trap_titles']) and 'engineer' not in t)
    
    return feat

def rank_features(feat):
    feat['final_score'] = 0.0
    feat['penalties'] = np.where(feat['is_inconsistent'] | feat['is_partial'], config['weights']['consistency_penalty'], 0.0)
    
    for k in ['title_affinity', 'skill_affinity', 'career_affinity', 'semantic_sim', 'bm25_score', 'quality_score']:
        feat['final_score'] += feat[k] * config['weights'][k]
        
    feat['final_score'] += feat['penalties']
        
    return feat.sort_values(by='final_score', ascending=False)

# 3. Execution & Export
metrics = {}

for jd_name, jd_data in base_jds.items():
    print(f"Executing {jd_name}...")
    start_time = time.time()
    
    feat_base = extract_features(df, jd_data)
    ranked = rank_features(feat_base)
    
    end_time = time.time()
    top100 = ranked.head(100)
    
    output_records = []
    for rank_idx, (_, row) in enumerate(top100.iterrows()):
        output_records.append({
            'rank': rank_idx + 1,
            'candidate_id': row['candidate_id'],
            'title': row['current_title'],
            'final_score': float(row['final_score']),
            'TitleAff_Contrib': float(row['title_affinity'] * config['weights']['title_affinity']),
            'SkillAff_Contrib': float(row['skill_affinity'] * config['weights']['skill_affinity']),
            'CareerAff_Contrib': float(row['career_affinity'] * config['weights']['career_affinity']),
            'SemSim_Contrib': float(row['semantic_sim'] * config['weights']['semantic_sim']),
            'BM25_Contrib': float(row['bm25_score'] * config['weights']['bm25_score']),
            'Quality_Contrib': float(row['quality_score'] * config['weights']['quality_score']),
            'Penalties': float(row['penalties'])
        })
    
    with open(os.path.join(archive_dir, f'top100_{jd_name.replace(" ", "_")}.json'), 'w') as f:
        json.dump(output_records, f, indent=2)
        
    metrics[jd_name] = {
        'Runtime_Seconds': end_time - start_time,
        'Honeypot_Pct': float((top100['is_trap'].sum() / 100.0) * 100),
        'Fully_Consistent_Pct': float((top100['is_consistent'].sum() / 100.0) * 100),
        'Partial_Conflict_Pct': float((top100['is_partial'].sum() / 100.0) * 100),
        'Full_Conflict_Pct': float((top100['is_inconsistent'].sum() / 100.0) * 100)
    }

with open(os.path.join(archive_dir, 'metrics_v1.json'), 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"Baselines successfully exported to {archive_dir}/")
