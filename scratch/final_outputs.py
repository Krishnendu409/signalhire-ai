import pandas as pd
import numpy as np
import lightgbm as lgb
import json
import sys
import os

sys.path.append('hackathon_pipeline')
from feature_extractor import extract_recruiter_features, FEATURE_COLS

def get_contributions(model, row):
    base_score = model.predict([row[FEATURE_COLS]])[0]
    
    # Semantic
    r = row.copy(); r['semantic_sim'] = 0.0
    sem_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    # BM25
    r = row.copy(); r['bm25_score'] = 0.0
    bm25_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    # Ontology (Search/Ranking/Embedding/VectorDB)
    r = row.copy()
    for col in ['retrieval_experience_score', 'ranking_experience_score', 'embedding_experience_score', 'vector_db_score']:
        r[col] = 0.0
    ont_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    # Production ML
    r = row.copy(); r['production_ml_score'] = 0.0
    prod_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    # Hireability & Soft Signals
    r = row.copy()
    for col in ['hireability_score', 'recruiter_interest_score', 'startup_readiness_score', 'leadership_score', 'product_ownership_score']:
        r[col] = 0.0
    hire_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0])
    
    # Keyword Trap Risk
    r = row.copy(); r['keyword_trap_risk'] = 0.0
    trap_drop = max(0, base_score - model.predict([r[FEATURE_COLS]])[0]) # this feature has 0 gain, so drop will be 0
    
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

def main():
    if not os.path.exists("submission.csv"):
        print("submission.csv not found")
        return
        
    df_sub = pd.read_csv("submission.csv")
    top100_ids = df_sub['candidate_id'].tolist()
    
    # Load Candidates
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
    # Ensure they are in the same order as submission
    df_cands['rank_order'] = df_cands['candidate_id'].apply(lambda x: top100_ids.index(x))
    df_cands = df_cands.sort_values('rank_order').reset_index(drop=True)
    
    print("\n" + "="*50)
    print("OUTPUT 1: TOP 20 INTERVIEWABILITY")
    print("="*50)
    yes_count = 0
    maybe_count = 0
    no_count = 0
    
    for i in range(20):
        c = df_cands.iloc[i]
        p = c.get('profile', {}) or {}
        title = p.get('current_title', '') or ''
        yrs = p.get('years_of_experience', 0)
        
        t_lower = title.lower()
        if yrs >= 4 and any(x in t_lower for x in ['search', 'nlp', 'ml', 'ai', 'data scientist', 'machine learning', 'retrieval', 'ranking']):
            yes_count += 1
        elif yrs >= 2 and any(x in t_lower for x in ['search', 'nlp', 'ml', 'ai', 'data scientist', 'machine learning', 'retrieval', 'ranking', 'engineer', 'developer', 'software']):
            maybe_count += 1
        else:
            no_count += 1
            
    print(f"YES: {yes_count}")
    print(f"MAYBE: {maybe_count}")
    print(f"NO: {no_count}")
    
    print("\n" + "="*50)
    print("OUTPUT 2: CANDIDATE CATEGORY DISTRIBUTION (TOP 100)")
    print("="*50)
    cats = {
        'Search Engineer': 0,
        'NLP Engineer': 0,
        'Applied ML Engineer': 0,
        'Recommendation Engineer': 0,
        'Software Engineer': 0,
        'Project Manager': 0,
        'Sales': 0,
        'Marketing': 0,
        'Other': 0
    }
    
    for i in range(100):
        c = df_cands.iloc[i]
        p = c.get('profile', {}) or {}
        title = p.get('current_title', '') or ''
        career = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in (c.get('career_history', []) or [])])
        cat = get_category(title, career)
        cats[cat] += 1
        
    for k, v in cats.items():
        if v > 0:
            print(f"{k}: {v}")
            
    print("\n" + "="*50)
    print("OUTPUT 3: FEATURE CONTRIBUTION AUDIT (TOP 10)")
    print("="*50)
    
    model = lgb.Booster(model_file="lgbm_ranker.txt")
    features_df = extract_recruiter_features(df_cands)
    # mock semantic and bm25
    features_df['semantic_sim'] = 0.8
    features_df['bm25_score'] = 0.8
    
    for i in range(10):
        cid = df_cands.iloc[i]['candidate_id']
        p = df_cands.iloc[i].get('profile', {}) or {}
        title = p.get('current_title', '') or ''
        pcts = get_contributions(model, features_df.iloc[i])
        print(f"[{i+1}] {cid} - {title}")
        print(f"BM25: {pcts[0]}% | Semantic: {pcts[1]}% | Ontology: {pcts[2]}% | Production ML: {pcts[3]}% | Hireability: {pcts[4]}% | Keyword Trap Risk: {pcts[5]}%")
        print("-" * 40)

if __name__ == "__main__":
    main()
