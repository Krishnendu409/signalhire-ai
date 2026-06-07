import json
import pandas as pd
import numpy as np

print("Running Feature Influence & Consistency Audit...")

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
    'Search Engineer': ['python', 'elasticsearch', 'faiss', 'machine learning', 'nlp', 'deep learning', 'pytorch', 'tensorflow'],
    'Frontend Engineer': ['javascript', 'react', 'css', 'html', 'typescript', 'ui/ux', 'vue', 'angular', 'redux'],
    'Sales Manager': ['sales', 'crm', 'b2b', 'negotiation', 'leadership', 'pipeline', 'salesforce', 'marketing']
}

base_jds = {
    'Search Engineer': {
        'family': 'Search Engineer',
        'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
        'title_terms': role_families['Search Engineer'],
        'req_skills': skill_families['Search Engineer'],
        'seniority_years': 5,
        'rel_regex': 'search engineer|retrieval engineer|nlp engineer|ranking engineer|ml ranking|ai research engineer|machine learning engineer'
    },
    'Frontend Engineer': {
        'family': 'Frontend Engineer',
        'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui', 'typescript'],
        'title_terms': role_families['Frontend Engineer'],
        'req_skills': skill_families['Frontend Engineer'],
        'seniority_years': 4,
        'rel_regex': 'frontend|front-end|web developer|ui developer'
    },
    'Sales Manager': {
        'family': 'Sales Manager',
        'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
        'title_terms': role_families['Sales Manager'],
        'req_skills': skill_families['Sales Manager'],
        'seniority_years': 6,
        'rel_regex': 'sales|account executive|business development'
    }
}

trap_titles = ['marketing', 'sales', 'hr', 'recruiter', 'manager', 'project manager', 'product manager', 'analyst', 'support', 'executive', 'director', 'accountant']

def extract_features(df_input, jd_data, is_sales=False):
    feat = df_input[['candidate_id', 'current_title', 'quality_score', 'skills_text', 'skills', 'desc_text']].copy()
    
    def ext_features(row):
        s_text = row['skills_text']
        d_text = row['desc_text']
        t_text = row['current_title']
        full = s_text + " " + d_text
        
        # 1. Affinity
        t_hits = sum(1 for w in jd_data['title_terms'] if w in t_text)
        taff = min(t_hits / 2.0, 1.0)
        
        sk_hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        saff = sk_hits / max(len(jd_data['req_skills']), 1)
        
        c_hits = sum(1 for k in jd_data['keywords'] if k in d_text)
        caff = c_hits / max(len(jd_data['keywords']), 1)
        
        # 2. Base 
        hits = sum(1 for k in jd_data['keywords'] if k in full)
        sem = hits / max(len(jd_data['keywords']), 1)
        bm25 = sem * 0.8
        
        # Consistency Check Stage
        # Candidate's natural family according to their text:
        cand_t_fam = max([(fam, sum(1 for w in terms if w in t_text)) for fam, terms in role_families.items()], key=lambda x: x[1])
        cand_s_fam = max([(fam, sum(1 for k in terms if k in s_text)) for fam, terms in skill_families.items()], key=lambda x: x[1])
        
        # JD Family agrees with Title AND Skill family?
        jd_fam = jd_data['family']
        
        consistency_penalty = 0.0
        # If candidate title strictly maps to a DIFFERENT known engineering/sales family, apply penalty
        if cand_t_fam[1] > 0 and cand_t_fam[0] != jd_fam:
            consistency_penalty = -20.0 # Huge penalty for contradictory title
        
        # If candidate skill strictly maps to a DIFFERENT family, apply penalty
        if cand_s_fam[1] > 2 and cand_s_fam[0] != jd_fam:
            consistency_penalty -= 20.0
            
        return pd.Series([sem, bm25, taff, saff, caff, consistency_penalty])
        
    feat[['semantic_sim', 'bm25_score', 'title_affinity', 'skill_affinity', 'career_affinity', 'consistency_penalty']] = feat.apply(ext_features, axis=1)
    
    feat['is_relevant'] = feat['current_title'].str.contains(jd_data['rel_regex'])
    if is_sales:
        feat['is_trap'] = feat['current_title'].str.contains('engineer|developer|scientist|data')
    else:
        feat['is_trap'] = feat['current_title'].apply(lambda t: any(tr in t for tr in trap_titles) and 'engineer' not in t)
    return feat

def rank_features(feat, drop_feature=None, apply_consistency=False):
    feat['final_score'] = 0.0
    w = {
        'title_affinity': 2.50,
        'skill_affinity': 3.50,
        'career_affinity': 2.50,
        'semantic_sim': 1.00,
        'quality_score': 1.00
    }
    
    if drop_feature and drop_feature in w:
        w[drop_feature] = 0.0
        
    for k, weight in w.items():
        feat['final_score'] += feat[k] * weight
        
    if apply_consistency:
        feat['final_score'] += feat['consistency_penalty']
        
    return feat.sort_values(by='final_score', ascending=False)

results = {}

for jd_name in base_jds.keys():
    print(f"\nProcessing {jd_name}...")
    is_sales = (jd_name == 'Sales Manager')
    
    feat_base = extract_features(df, base_jds[jd_name], is_sales)
    
    all_rel_cnt = feat_base['is_relevant'].sum()
    
    r_base = rank_features(feat_base.copy())
    r_consist = rank_features(feat_base.copy(), apply_consistency=True)
    
    # Feature Ablations for #1 stability
    r_no_title = rank_features(feat_base.copy(), drop_feature='title_affinity')
    r_no_skill = rank_features(feat_base.copy(), drop_feature='skill_affinity')
    r_no_career = rank_features(feat_base.copy(), drop_feature='career_affinity')
    r_no_sem = rank_features(feat_base.copy(), drop_feature='semantic_sim')
    
    base_rank1 = r_base.iloc[0]['candidate_id']
    
    def rank1_changed(r_ablated):
        return r_ablated.iloc[0]['candidate_id'] != base_rank1
        
    def get_metrics(ranked_df):
        top100 = ranked_df.head(100)
        rel_in_100 = top100['is_relevant'].sum()
        rec100 = rel_in_100 / all_rel_cnt if all_rel_cnt > 0 else 0
        trap_pen = (top100['is_trap'].sum() / 100) * 100
        return rec100, trap_pen

    base_rec, base_trap = get_metrics(r_base)
    consist_rec, consist_trap = get_metrics(r_consist)
    
    results[jd_name] = {
        'Baseline_Affinity': {
            'Recall': base_rec,
            'Honeypot': base_trap
        },
        'Consistency_Checked': {
            'Recall': consist_rec,
            'Honeypot': consist_trap
        },
        'Rank_1_Stability': {
            'Changed_without_TitleAff': rank1_changed(r_no_title),
            'Changed_without_SkillAff': rank1_changed(r_no_skill),
            'Changed_without_CareerAff': rank1_changed(r_no_career),
            'Changed_without_SemanticSim': rank1_changed(r_no_sem)
        }
    }
    
    # Hidden Title Stress Test for Consistency
    # Sales Manager -> Customer Success Lead
    if jd_name == 'Sales Manager':
        jd_hidden = {**base_jds['Sales Manager'], 'title_terms': ['customer success', 'lead']}
        feat_hid = extract_features(df, jd_hidden, True)
        # Without consistency
        r_hid_base = rank_features(feat_hid.copy())
        # With consistency
        r_hid_consist = rank_features(feat_hid.copy(), apply_consistency=True)
        
        results['Sales_CustomerSuccess_Stress'] = {
            'Baseline_Honeypot': get_metrics(r_hid_base)[1],
            'Consistency_Honeypot': get_metrics(r_hid_consist)[1]
        }
        
    # Search Engineer -> Revenue Operations Manager
    if jd_name == 'Search Engineer':
        jd_hidden = {**base_jds['Search Engineer'], 'title_terms': ['revenue operations', 'manager']}
        feat_hid = extract_features(df, jd_hidden, False)
        # Without consistency
        r_hid_base = rank_features(feat_hid.copy())
        # With consistency
        r_hid_consist = rank_features(feat_hid.copy(), apply_consistency=True)
        
        results['Search_RevOps_Stress'] = {
            'Baseline_Honeypot': get_metrics(r_hid_base)[1],
            'Consistency_Honeypot': get_metrics(r_hid_consist)[1]
        }

with open('influence_audit_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nAudit Complete.")
