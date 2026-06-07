import pandas as pd
import numpy as np
import lightgbm as lgb
import json
import sys
import os
import re

sys.path.append('hackathon_pipeline')
from feature_extractor import extract_recruiter_features, FEATURE_COLS

def get_contributions(model, row):
    base_score = model.predict([row[FEATURE_COLS]])[0]
    
    r = row.copy(); r['semantic_sim'] = 0.0
    sem_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    r = row.copy(); r['bm25_score'] = 0.0
    bm25_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    r = row.copy()
    for col in ['retrieval_experience_score', 'ranking_experience_score', 'embedding_experience_score', 'vector_db_score']:
        r[col] = 0.0
    ont_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    r = row.copy(); r['production_ml_score'] = 0.0
    prod_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    r = row.copy()
    for col in ['hireability_score', 'recruiter_interest_score', 'startup_readiness_score', 'leadership_score', 'product_ownership_score']:
        r[col] = 0.0
    hire_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    r = row.copy(); r['keyword_trap_risk'] = 0.0
    trap_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    drops = np.array([bm25_drop, sem_drop, ont_drop, prod_drop, hire_drop, trap_drop])
    total = np.sum(drops)
    if total == 0: return [0]*6
    return np.round((drops / total) * 100).astype(int)

def get_category(title, career_text):
    t = title.lower()
    c = career_text.lower()
    if 'search' in t or 'search' in c or 'retrieval' in t or 'retrieval' in c:
        return 'Search Engineer'
    elif 'nlp' in t or 'nlp' in c or 'natural language' in t or 'natural language' in c:
        return 'NLP Engineer'
    elif 'recommend' in t or 'recommend' in c or 'ranking' in t or 'ranking' in c:
        return 'Recommendation Engineer'
    elif 'machine learning' in t or 'ml' in t or 'machine learning' in c or 'ml ' in c:
        return 'Applied ML Engineer'
    elif 'software' in t or 'developer' in t or 'backend' in t:
        return 'Software Engineer'
    elif 'project' in t or 'product manager' in t or 'program manager' in t:
        return 'Project Manager'
    elif 'sales' in t or 'account' in t or 'business' in t:
        return 'Sales'
    elif 'market' in t or 'seo' in t:
        return 'Marketing'
    else:
        return 'Other'

def find_triggers(cand):
    # Same as feature_extractor.py
    blocks = []
    p = cand.get('profile', {}) or {}
    blocks.append(p.get('headline', '') or '')
    blocks.append(p.get('summary', '') or '')
    blocks.append(p.get('current_title', '') or '')
    
    skills = cand.get('skills', []) or []
    for s in skills:
        if isinstance(s, dict):
            blocks.append(s.get('name', '') or '')
            
    career = cand.get('career_history', []) or []
    for j in career:
        if isinstance(j, dict):
            blocks.append(j.get('title', '') or '')
            blocks.append(j.get('description', '') or '')
            
    text = " ".join(blocks).lower()
    
    keywords = [
        'deployed', 'production', 'serving', 'inference',
        'monitoring', 'mlops', 'ci/cd', 'docker', 'kubernetes',
        'aws sagemaker', 'ml pipeline', 'model serving',
        'latency', 'throughput', 'scalab'
    ]
    
    found = []
    for k in keywords:
        matches = re.finditer(r'\b' + re.escape(k) + r'\b', text)
        for m in matches:
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            context = text[start:end].replace('\n', ' ')
            found.append(f"'{k}' found in: \"...{context}...\"")
            
    # Also without word boundaries for 'scalab'
    for k in ['scalab']:
        matches = re.finditer(re.escape(k), text)
        for m in matches:
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            context = text[start:end].replace('\n', ' ')
            found.append(f"'{k}' found in: \"...{context}...\"")
            
    # Return unique found contexts (up to 5)
    return list(set(found))[:5]

def main():
    df_sub = pd.read_csv("submission.csv")
    top100_ids = df_sub['candidate_id'].tolist()
    
    cands_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(cands_path):
        cands_path = r"../" + cands_path
        
    top100_cands = []
    with open(cands_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                c = json.loads(line)
                if c['candidate_id'] in top100_ids:
                    top100_cands.append(c)
            except: pass
            
    df_cands = pd.DataFrame(top100_cands)
    df_cands['rank_order'] = df_cands['candidate_id'].apply(lambda x: top100_ids.index(x))
    df_cands = df_cands.sort_values('rank_order').reset_index(drop=True)
    
    model = lgb.Booster(model_file="lgbm_ranker.txt")
    features_df = extract_recruiter_features(df_cands)
    features_df['semantic_sim'] = 0.8
    features_df['bm25_score'] = 0.8
    
    print("\n" + "="*50)
    print("TOP 10 BAD CANDIDATES FEATURE DUMP")
    print("="*50)
    
    bad_count = 0
    for i in range(100):
        c = df_cands.iloc[i]
        p = c.get('profile', {}) or {}
        title = p.get('current_title', '') or ''
        career = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in (c.get('career_history', []) or [])])
        cat = get_category(title, career)
        
        if cat in ['Project Manager', 'Sales', 'Marketing', 'HR Manager', 'Operations Manager', 'Content Writer', 'Customer Support']:
            if bad_count >= 10: break
            bad_count += 1
            f = features_df.iloc[i]
            print(f"\n[{i+1}] {c['candidate_id']} - {title}")
            print(f"  production_ml_score: {f['production_ml_score']:.2f}")
            print(f"  hireability_score: {f['hireability_score']:.2f}")
            print(f"  retrieval_experience_score: {f['retrieval_experience_score']:.2f}")
            print(f"  ranking_experience_score: {f['ranking_experience_score']:.2f}")
            print(f"  vector_db_score: {f['vector_db_score']:.2f}")
            print(f"  semantic_sim (simulated): {f['semantic_sim']:.2f}")
            cand_dict = next(cand for cand in top100_cands if cand['candidate_id'] == c['candidate_id'])
            triggers = find_triggers(cand_dict)
            print("  Triggered because:")
            for t in triggers:
                print(f"    - {t}")
                
    print("\n" + "="*50)
    print("SEARCH ENGINEER PERFORMANCE")
    print("="*50)
    
    se_ranks = []
    best_se = None
    best_se_idx = -1
    
    for i in range(100):
        c = df_cands.iloc[i]
        p = c.get('profile', {}) or {}
        title = p.get('current_title', '') or ''
        career = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in (c.get('career_history', []) or [])])
        cat = get_category(title, career)
        
        if cat == 'Search Engineer':
            se_ranks.append(i + 1)
            if best_se is None:
                best_se = c
                best_se_idx = i
                
    if se_ranks:
        print(f"Average Rank of Search Engineers: {np.mean(se_ranks):.1f}")
        print(f"Highest-Ranked Search Engineer: Rank {best_se_idx + 1}")
        
        p = best_se.get('profile', {}) or {}
        title = p.get('current_title', '') or ''
        f = features_df.iloc[best_se_idx]
        print(f"\n  Title: {title}")
        print(f"  production_ml_score: {f['production_ml_score']:.2f}")
        print(f"  hireability_score: {f['hireability_score']:.2f}")
        print(f"  retrieval_experience_score: {f['retrieval_experience_score']:.2f}")
        
        pcts = get_contributions(model, f)
        print("\n  Feature Contributions:")
        print(f"  BM25: {pcts[0]}% | Semantic: {pcts[1]}% | Ontology: {pcts[2]}% | Production ML: {pcts[3]}% | Hireability: {pcts[4]}%")
    else:
        print("No Search Engineers found in Top 100.")

if __name__ == "__main__":
    main()
