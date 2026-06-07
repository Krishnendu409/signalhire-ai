import json
import pandas as pd
import numpy as np
import copy

print("Running Extensive Feature Influence & Consistency Audit V3...")

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

role_families = {
    'Search Engineer': ['search', 'retrieval', 'relevance', 'ranking', 'nlp', 'machine learning', 'ai', 'data scientist', 'ml'],
    'Frontend Engineer': ['frontend', 'ui', 'ux', 'client', 'web', 'javascript', 'react', 'angular', 'vue', 'front-end'],
    'Sales Manager': ['sales', 'revenue', 'account', 'business development', 'gtm', 'growth', 'customer success', 'marketing', 'manager', 'executive']
}

skill_families = {
    'Search Engineer': ['python', 'elasticsearch', 'faiss', 'machine learning', 'nlp', 'deep learning', 'pytorch', 'tensorflow', 'scikit-learn'],
    'Frontend Engineer': ['javascript', 'react', 'css', 'html', 'typescript', 'ui/ux', 'vue', 'angular', 'redux', 'next.js'],
    'Sales Manager': ['sales', 'crm', 'b2b', 'negotiation', 'leadership', 'pipeline', 'salesforce', 'marketing', 'quota']
}

base_jds = {
    'Search Engineer': {
        'family': 'Search Engineer',
        'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
        'title_terms': role_families['Search Engineer'],
        'req_skills': skill_families['Search Engineer']
    },
    'Frontend Engineer': {
        'family': 'Frontend Engineer',
        'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui', 'typescript'],
        'title_terms': role_families['Frontend Engineer'],
        'req_skills': skill_families['Frontend Engineer']
    },
    'Sales Manager': {
        'family': 'Sales Manager',
        'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
        'title_terms': role_families['Sales Manager'],
        'req_skills': skill_families['Sales Manager']
    }
}

trap_titles = ['marketing', 'sales', 'hr', 'recruiter', 'manager', 'project manager', 'product manager', 'analyst', 'support', 'executive', 'director', 'accountant']

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
        
        cand_t_fam = max([(fam, sum(1 for w in terms if w in t_text)) for fam, terms in role_families.items()], key=lambda x: x[1])
        cand_s_fam = max([(fam, sum(1 for k in terms if k in s_text)) for fam, terms in skill_families.items()], key=lambda x: x[1])
        cand_c_fam = max([(fam, sum(1 for k in terms if k in d_text)) for fam, terms in skill_families.items()], key=lambda x: x[1])
        
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
        feat['is_trap'] = feat['current_title'].apply(lambda t: any(tr in t for tr in trap_titles) and 'engineer' not in t)
    
    return feat

def rank_features(feat, drop_feature=None, penalty=0.0):
    feat['final_score'] = 0.0
    w = {
        'title_affinity': 2.50,
        'skill_affinity': 3.50,
        'career_affinity': 2.50,
        'semantic_sim': 1.00,
        'bm25_score': 1.00,
        'quality_score': 1.00
    }
    
    if drop_feature and drop_feature in w:
        w[drop_feature] = 0.0
        
    for k, weight in w.items():
        feat['final_score'] += feat[k] * weight
        
    if penalty < 0:
        feat['final_score'] += np.where(feat['is_inconsistent'] | feat['is_partial'], penalty, 0.0)
        
    return feat.sort_values(by='final_score', ascending=False)

results = {'Section1_FeatureInfluence': {}, 'Section2_Consistency': {}, 'Section3_ContradictionStress': {}, 'Section4_PenaltySimulation': {}}

for jd_name, jd_data in base_jds.items():
    print(f"\nProcessing {jd_name}...")
    feat_base = extract_features(df, jd_data)
    
    r_base = rank_features(feat_base.copy())
    top100_base = r_base.head(100)
    top10_base_ids = set(r_base.head(10)['candidate_id'])
    top100_base_ids = set(top100_base['candidate_id'])
    
    # Section 1A: Rank 1 Sensitivity
    def evaluate_ablation(drop_feat):
        r_abl = rank_features(feat_base.copy(), drop_feature=drop_feat)
        r1_changed = (r_abl.iloc[0]['candidate_id'] != r_base.iloc[0]['candidate_id'])
        t10_overlap = len(top10_base_ids.intersection(set(r_abl.head(10)['candidate_id'])))
        t100_overlap = len(top100_base_ids.intersection(set(r_abl.head(100)['candidate_id'])))
        return {'Rank_1_Changed': r1_changed, 'Top10_Overlap': t10_overlap, 'Top100_Overlap': t100_overlap}
        
    results['Section1_FeatureInfluence'][jd_name] = {
        'Ablation': {
            'No_TitleAff': evaluate_ablation('title_affinity'),
            'No_SkillAff': evaluate_ablation('skill_affinity'),
            'No_CareerAff': evaluate_ablation('career_affinity'),
            'No_SemSim': evaluate_ablation('semantic_sim'),
            'No_BM25': evaluate_ablation('bm25_score')
        },
        'Top20_Contribution': []
    }
    
    # Section 1B: Top 20 Decomposition
    w = {'title_affinity': 2.5, 'skill_affinity': 3.5, 'career_affinity': 2.5, 'semantic_sim': 1.0, 'bm25_score': 1.0}
    for _, row in r_base.head(20).iterrows():
        results['Section1_FeatureInfluence'][jd_name]['Top20_Contribution'].append({
            'candidate_id': row['candidate_id'],
            'title': row['current_title'],
            'final_score': row['final_score'],
            'TitleAff_Contrib': row['title_affinity'] * w['title_affinity'],
            'SkillAff_Contrib': row['skill_affinity'] * w['skill_affinity'],
            'CareerAff_Contrib': row['career_affinity'] * w['career_affinity'],
            'SemSim_Contrib': row['semantic_sim'] * w['semantic_sim'],
            'BM25_Contrib': row['bm25_score'] * w['bm25_score']
        })
        
    # Section 2: Consistency Audit
    results['Section2_Consistency'][jd_name] = {
        'Fully_Consistent_Pct': (top100_base['is_consistent'].sum() / 100.0) * 100,
        'Partial_Conflict_Pct': (top100_base['is_partial'].sum() / 100.0) * 100,
        'Full_Conflict_Pct': (top100_base['is_inconsistent'].sum() / 100.0) * 100
    }

# Section 3: Contradiction Stress Tests
stress_tests = [
    ('Sales Manager', 'Information Retrieval Engineer', ['information', 'retrieval', 'engineer']),
    ('Sales Manager', 'UI Engineer', ['ui', 'engineer']),
    ('Sales Manager', 'Machine Learning Engineer', ['machine', 'learning', 'engineer', 'ml']),
    ('Frontend Engineer', 'Revenue Operations Manager', ['revenue', 'operations', 'manager', 'revops']),
    ('Frontend Engineer', 'Customer Success Lead', ['customer', 'success', 'lead']),
    ('Search Engineer', 'Revenue Operations Manager', ['revenue', 'operations', 'manager', 'revops'])
]

for jd_name, display_name, override_terms in stress_tests:
    jd_hidden = copy.deepcopy(base_jds[jd_name])
    jd_hidden['title_terms'] = override_terms
    feat_hid = extract_features(df, jd_hidden)
    
    r_hid = rank_features(feat_hid.copy())
    top100 = r_hid.head(100)
    
    results['Section3_ContradictionStress'][f"{jd_name} + {display_name}"] = {
        'Honeypot_Pct': (top100['is_trap'].sum() / 100.0) * 100,
        'Full_Conflict_Pct': (top100['is_inconsistent'].sum() / 100.0) * 100
    }

# Section 4: Consistency Penalty Simulation
# The user wants us to run the stress tests WITH consistency penalties, to see if it fixes the blindness!
results['Section4_PenaltySimulation'] = {}
for jd_name, display_name, override_terms in stress_tests:
    jd_hidden = copy.deepcopy(base_jds[jd_name])
    jd_hidden['title_terms'] = override_terms
    feat_hid = extract_features(df, jd_hidden)
    results['Section4_PenaltySimulation'][f"{jd_name} + {display_name}"] = {}
    
    for pen in [-1, -2, -4, -8]:
        r_pen = rank_features(feat_hid.copy(), penalty=pen)
        top100 = r_pen.head(100)
        
        results['Section4_PenaltySimulation'][f"{jd_name} + {display_name}"][f"Penalty_{pen}"] = {
            'Honeypot_Pct': (top100['is_trap'].sum() / 100.0) * 100
        }

with open('audit_v3_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nAudit Complete.")
