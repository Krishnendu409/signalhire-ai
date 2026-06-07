import json
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os

print("Running Domain Affinity Audit...")

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

print("Loading model and embeddings...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# To save time, we will embed the JD texts, and we will embed the candidate texts on the fly for a subset or all.
# Actually, since embedding 100k takes a few minutes, we'll embed the candidate Title, Skills, and Desc separately 
# in batches. Wait, let's just do a fast keyword-ecosystem approach for affinity if embedding takes too long, OR
# use a predefined set of role family keywords.
# "understand role families rather than exact title strings"
# Let's use role family mapping for title affinity.
role_families = {
    'Search Engineer': ['search', 'retrieval', 'relevance', 'ranking', 'nlp', 'machine learning', 'ai', 'data scientist'],
    'Frontend Engineer': ['frontend', 'ui', 'ux', 'client', 'web', 'javascript', 'react', 'angular', 'vue'],
    'Sales Manager': ['sales', 'revenue', 'account', 'business development', 'gtm', 'growth', 'customer success', 'marketing']
}

base_jds = {
    'Search Engineer': {
        'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
        'title_terms': role_families['Search Engineer'],
        'req_skills': ['python', 'elasticsearch', 'faiss', 'machine learning', 'nlp', 'deep learning'],
        'seniority_years': 5,
        'rel_regex': 'search engineer|retrieval engineer|nlp engineer|ranking engineer|ml ranking|ai research engineer|machine learning engineer'
    },
    'Frontend Engineer': {
        'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui', 'typescript'],
        'title_terms': role_families['Frontend Engineer'],
        'req_skills': ['javascript', 'react', 'css', 'html', 'typescript', 'ui/ux'],
        'seniority_years': 4,
        'rel_regex': 'frontend|front-end|web developer|ui developer'
    },
    'Sales Manager': {
        'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
        'title_terms': role_families['Sales Manager'],
        'req_skills': ['sales', 'crm', 'b2b', 'negotiation', 'leadership', 'pipeline management'],
        'seniority_years': 6,
        'rel_regex': 'sales|account executive|business development'
    }
}

hidden_title_jds = {
    'Search Engineer': {
        'Revenue Operations Manager': {**base_jds['Search Engineer'], 'title_terms': ['revenue operations', 'manager']},
        'Customer Success Lead': {**base_jds['Search Engineer'], 'title_terms': ['customer success', 'lead']},
        'Product Marketing Manager': {**base_jds['Search Engineer'], 'title_terms': ['product marketing', 'manager']},
        'Information Retrieval Engineer': {**base_jds['Search Engineer'], 'title_terms': ['information retrieval', 'engineer']},
        'UI Engineer': {**base_jds['Search Engineer'], 'title_terms': ['ui', 'engineer']}
    },
    'Frontend Engineer': {
        'Revenue Operations Manager': {**base_jds['Frontend Engineer'], 'title_terms': ['revenue operations', 'manager']},
        'Customer Success Lead': {**base_jds['Frontend Engineer'], 'title_terms': ['customer success', 'lead']},
        'Product Marketing Manager': {**base_jds['Frontend Engineer'], 'title_terms': ['product marketing', 'manager']},
        'Information Retrieval Engineer': {**base_jds['Frontend Engineer'], 'title_terms': ['information retrieval', 'engineer']},
        'UI Engineer': {**base_jds['Frontend Engineer'], 'title_terms': ['ui', 'engineer']}
    },
    'Sales Manager': {
        'Revenue Operations Manager': {**base_jds['Sales Manager'], 'title_terms': ['revenue operations', 'manager']},
        'Customer Success Lead': {**base_jds['Sales Manager'], 'title_terms': ['customer success', 'lead']},
        'Product Marketing Manager': {**base_jds['Sales Manager'], 'title_terms': ['product marketing', 'manager']},
        'Information Retrieval Engineer': {**base_jds['Sales Manager'], 'title_terms': ['information retrieval', 'engineer']},
        'UI Engineer': {**base_jds['Sales Manager'], 'title_terms': ['ui', 'engineer']}
    }
}

trap_titles = ['marketing', 'sales', 'hr', 'recruiter', 'manager', 'project manager', 'product manager', 'analyst', 'support', 'executive', 'director', 'accountant']

def extract_features(df_input, jd_data, is_sales=False):
    feat = df_input[['candidate_id', 'current_title', 'current_company', 'quality_score', 'skills_text', 'skills']].copy()
    
    def ext_features(row):
        s_text = row['skills_text']
        d_text = df_input.loc[row.name, 'desc_text']
        t_text = row['current_title']
        full = s_text + " " + d_text
        
        # 1. Title Affinity (Ecosystem)
        t_hits = sum(1 for w in jd_data['title_terms'] if w in t_text)
        taff = min(t_hits / 2.0, 1.0)
        
        # 2. Skill Affinity
        sk_hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        saff = sk_hits / max(len(jd_data['req_skills']), 1)
        
        # 3. Career Affinity (Description overlap with keywords)
        c_hits = sum(1 for k in jd_data['keywords'] if k in d_text)
        caff = c_hits / max(len(jd_data['keywords']), 1)
        
        # Base Sem/BM25
        hits = sum(1 for k in jd_data['keywords'] if k in full)
        sem = hits / max(len(jd_data['keywords']), 1)
        bm25 = sem * 0.8
        
        trap = 1.0 if (bm25 > 0.6 and taff == 0) else 0.0
        
        return pd.Series([sem, bm25, taff, saff, caff, trap])
        
    feat[['semantic_sim', 'bm25_score', 'title_affinity', 'skill_affinity', 'career_affinity', 'keyword_trap_penalty']] = feat.apply(ext_features, axis=1)
    
    feat['is_relevant'] = feat['current_title'].str.contains(jd_data['rel_regex'])
    if is_sales:
        feat['is_trap'] = feat['current_title'].str.contains('engineer|developer|scientist')
    else:
        feat['is_trap'] = feat['current_title'].apply(lambda t: any(tr in t for tr in trap_titles) and 'engineer' not in t)
    return feat

def rank_features(feat, apply_affinity=False):
    feat['final_score'] = 0.0
    if apply_affinity:
        # Affinity Weights
        w = {
            'title_affinity': 2.50,
            'skill_affinity': 3.50,
            'career_affinity': 2.50,
            'semantic_sim': 1.00,
            'quality_score': 1.00,
            'keyword_trap_penalty': -8.00
        }
    else:
        # Redistributed Baseline
        w = {
            'title_affinity': 2.50,   # acts as title_sim
            'semantic_sim': 3.50,
            'bm25_score': 2.50,
            'skill_affinity': 3.00,   # acts as skill_cov
            'quality_score': 1.00,
            'keyword_trap_penalty': -8.00 
        }
        
    for k, weight in w.items():
        feat['final_score'] += feat[k] * weight
    return feat.sort_values(by='final_score', ascending=False)

results = {}

def get_entropy(top100_df):
    titles = top100_df['current_title'].value_counts()
    p_t = titles / titles.sum()
    ent_title = -np.sum(p_t * np.log2(p_t + 1e-9))
    return ent_title

for jd_name in base_jds.keys():
    print(f"\nProcessing {jd_name}...")
    is_sales = (jd_name == 'Sales Manager')
    
    feat_base = extract_features(df, base_jds[jd_name], is_sales)
    all_rel_cnt = feat_base['is_relevant'].sum()
    
    # 1. Standard Benchmark
    r_redist = rank_features(feat_base.copy(), apply_affinity=False)
    r_aff = rank_features(feat_base.copy(), apply_affinity=True)
    
    def get_metrics(ranked_df):
        top100 = ranked_df.head(100)
        rel_in_100 = top100['is_relevant'].sum()
        rec100 = rel_in_100 / all_rel_cnt if all_rel_cnt > 0 else 0
        trap_pen = (top100['is_trap'].sum() / 100) * 100
        ent = get_entropy(top100)
        return rec100, trap_pen, ent

    b_rec, b_trap, b_ent = get_metrics(r_redist)
    a_rec, a_trap, a_ent = get_metrics(r_aff)
    
    results[jd_name] = {
        'total_relevant': int(all_rel_cnt),
        'Redistributed_Base': {'Recall': b_rec, 'Honeypot': b_trap, 'Title_Entropy': b_ent},
        'Affinity_Model': {'Recall': a_rec, 'Honeypot': a_trap, 'Title_Entropy': a_ent},
        'Hidden_Titles_Affinity': {}
    }
    
    # 2. Hidden Title Tests
    for test_title, jd_test_data in hidden_title_jds[jd_name].items():
        feat_hid = extract_features(df, jd_test_data, is_sales)
        r_hid_aff = rank_features(feat_hid.copy(), apply_affinity=True)
        h_rec, h_trap, h_ent = get_metrics(r_hid_aff)
        results[jd_name]['Hidden_Titles_Affinity'][test_title] = {
            'Recall': h_rec,
            'Honeypot': h_trap,
            'Title_Entropy': h_ent
        }

with open('domain_affinity_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nAudit Complete.")
