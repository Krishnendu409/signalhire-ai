import json
import pandas as pd
import numpy as np
import lightgbm as lgb
import sys
import os
import re

sys.path.append('hackathon_pipeline')
from feature_extractor import extract_recruiter_features, FEATURE_COLS

def old_score_keywords_bounded(text_blocks, keywords):
    score = 0.0
    sorted_kw = sorted(keywords, key=len, reverse=True)
    for text, weight in text_blocks:
        if not text:
            continue
        t = text.lower()
        for kw in sorted_kw:
            matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', t))
            if matches > 0:
                score += (matches * weight * 0.5)
                t = re.sub(r'\b' + re.escape(kw) + r'\b', '', t)
    return min(score, 10.0)

def old_prod_ml_score(cand):
    p = cand.get('profile', {}) or {}
    headline = p.get('headline', '') or ''
    summary = p.get('summary', '') or ''
    current_job = ""
    past_jobs = ""
    career = cand.get('career_history', []) or []
    if career:
        current_job = f"{career[0].get('title', '')} {career[0].get('description', '')}"
        past_jobs = " ".join([f"{j.get('title', '')} {j.get('description', '')}" for j in career[1:]])
    skills = " ".join([s.get('name', '') for s in (cand.get('skills', []) or [])])
    
    text_blocks = [
        (headline, 2.0),
        (summary, 1.5),
        (current_job, 1.5),
        (past_jobs, 1.0),
        (skills, 2.0)
    ]
    
    keywords = [
        'deployed', 'production', 'serving', 'inference',
        'monitoring', 'mlops', 'ci/cd', 'docker', 'kubernetes',
        'aws sagemaker', 'ml pipeline', 'model serving',
        'latency', 'throughput', 'scalab'
    ]
    return old_score_keywords_bounded(text_blocks, keywords)

def get_triggers(cand):
    pos_keywords = [
        'model serving', 'model deployment', 'inference', 'inference latency', 
        'feature store', 'serving infrastructure', 'online inference', 
        'real-time inference', 'batch inference', 'mlops', 'sagemaker', 
        'kubeflow', 'triton', 'tensorrt', 'airflow', 'model registry', 
        'canary deployment', 'shadow deployment', 'production model', 
        'production ml', 'serving stack', 'ml pipeline'
    ]
    p = cand.get('profile', {}) or {}
    headline = p.get('headline', '') or ''
    summary = p.get('summary', '') or ''
    career = cand.get('career_history', []) or []
    skills = " ".join([s.get('name', '') for s in (cand.get('skills', []) or [])])
    career_text = " ".join([f"{j.get('title', '')} {j.get('description', '')}" for j in career])
    
    text_lower = f"{headline} {summary} {career_text} {skills}".lower()
    
    neg_keywords = [
        'video production', 'film production', 'content production', 
        'manufacturing production', 'production scale-up', 'agency production', 
        'packaging production', 'media production', 'print production', 'audio production'
    ]
    for neg in neg_keywords:
        text_lower = text_lower.replace(neg, "")
        
    found = []
    for k in pos_keywords:
        matches = re.finditer(r'\b' + re.escape(k) + r'\b', text_lower)
        for m in matches:
            start = max(0, m.start() - 30)
            end = min(len(text_lower), m.end() + 30)
            context = text_lower[start:end].replace('\n', ' ')
            found.append(f"'{k}' found in: \"...{context}...\"")
    return list(set(found))[:5]

def main():
    print("Loading 10k candidates...")
    cands_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(cands_path):
        cands_path = r"../" + cands_path
        
    cands = []
    with open(cands_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 10000: break
            if not line.strip(): continue
            try:
                cands.append(json.loads(line))
            except: pass
            
    df_cands = pd.DataFrame(cands)
    print("Extracting features with NEW definition...")
    feat_df = extract_recruiter_features(df_cands)
    feat_df['semantic_sim'] = 0.8
    feat_df['bm25_score'] = 0.8
    
    print("\n" + "="*50)
    print("PRODUCTION FEATURE AUDIT (TOP 50)")
    print("="*50)
    top_50_idx = feat_df['production_ml_score'].nlargest(50).index
    for idx in top_50_idx:
        c = cands[idx]
        title = c.get('profile', {}).get('current_title', '')
        score = feat_df.loc[idx, 'production_ml_score']
        if score == 0: break
        triggers = get_triggers(c)
        print(f"[{score:.1f}] {c['candidate_id']} - {title}")
        for t in triggers:
            print(f"    - {t}")
            
    print("\n" + "="*50)
    print("ELITE CANDIDATES IMPACT")
    print("="*50)
    
    elite_ids = ['CAND_0005260', 'CAND_0009024', 'CAND_0009691', 'CAND_0008239']
    model = lgb.Booster(model_file="lgbm_ranker.txt")
    
    for eid in elite_ids:
        # find cand in the 10k if exists
        idx = None
        for i, c in enumerate(cands):
            if c['candidate_id'] == eid:
                idx = i
                break
        
        if idx is not None:
            c = cands[idx]
            old_prod = old_prod_ml_score(c)
            new_prod = feat_df.loc[idx, 'production_ml_score']
            
            # Predict old score
            f_old = feat_df.iloc[idx].copy()
            f_old['production_ml_score'] = old_prod
            old_total = model.predict([f_old[FEATURE_COLS]])[0]
            
            # Predict new score
            f_new = feat_df.iloc[idx].copy()
            f_new['production_ml_score'] = new_prod
            new_total = model.predict([f_new[FEATURE_COLS]])[0]
            
            title = c.get('profile', {}).get('current_title', '')
            print(f"{eid} - {title}")
            print(f"  Old Prod Score: {old_prod:.1f} -> New Prod Score: {new_prod:.1f}")
            print(f"  Old Total Score: {old_total:.1f} -> New Total Score: {new_total:.1f}\n")

if __name__ == "__main__":
    main()
