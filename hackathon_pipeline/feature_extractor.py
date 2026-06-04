import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
import re

def _score_keywords(text_blocks, keywords):
    """
    text_blocks is a list of tuples: (text, weight)
    keywords is a list of strings
    """
    score = 0.0
    for text, weight in text_blocks:
        if not text: continue
        t = text.lower()
        for kw in keywords:
            if kw.lower() in t:
                score += weight
    return score

def extract_recruiter_features(df):
    """
    Complete feature engineering overhaul based on Recruiter logic and JD requirements.
    """
    df = df.copy()
    features = pd.DataFrame(index=df.index)
    today = datetime(2026, 1, 1)
    
    for idx, row in df.iterrows():
        # --- PREPARE TEXT BLOCKS FOR WEIGHTED SCORING ---
        headline = row.get('headline', '') or ''
        summary = row.get('summary', '') or ''
        skills_text = " ".join([s.get('name', '') for s in row.get('skills', [])])
        
        career = row.get('career_history', [])
        # Sort career descending by end_date ideally, but assume it's chronological or reverse
        # We'll treat the first item as most recent if it has no end_date or highest end_date
        current_job_text = ""
        past_jobs_text = ""
        if career:
            # Assuming first in list is most recent
            current_job_text = (career[0].get('title', '') + " " + career[0].get('description', '')).lower()
            if len(career) > 1:
                past_jobs_text = " ".join([(j.get('title', '') + " " + j.get('description', '')) for j in career[1:]]).lower()
                
        # Weights: Headline/Summary (1.5), Current Job (2.0), Past Jobs (1.0), Skills (1.0)
        text_blocks = [
            (headline + " " + summary, 1.5),
            (current_job_text, 2.0),
            (past_jobs_text, 1.0),
            (skills_text, 1.0)
        ]
        
        # --- 1. Retrieval Experience Score ---
        features.at[idx, 'retrieval_experience_score'] = _score_keywords(text_blocks, 
            ['retrieval', 'search', 'semantic search', 'ranking', 'matching', 'information retrieval'])
            
        # --- 2. Ranking Experience Score ---
        features.at[idx, 'ranking_experience_score'] = _score_keywords(text_blocks,
            ['ranking', 'learning-to-rank', 'recommendation systems', 'lambdamart', 'xgboost ranker', 'candidate ranking', 'search ranking'])
            
        # --- 3. Embedding Experience Score ---
        features.at[idx, 'embedding_experience_score'] = _score_keywords(text_blocks,
            ['embedding', 'sentence transformer', 'bge', 'e5', 'vectorization', 'semantic similarity'])
            
        # --- 4. Vector DB Score ---
        features.at[idx, 'vector_db_score'] = _score_keywords(text_blocks,
            ['pinecone', 'qdrant', 'milvus', 'weaviate', 'faiss', 'elasticsearch', 'opensearch'])
            
        # --- 5. Evaluation Framework Score ---
        features.at[idx, 'evaluation_framework_score'] = _score_keywords(text_blocks,
            ['ndcg', 'mrr', 'map', 'a/b testing', 'ranking evaluation'])
            
        # --- 6. Production ML Score ---
        features.at[idx, 'production_ml_score'] = _score_keywords(text_blocks,
            ['deployed', 'production', 'serving', 'inference', 'monitoring', 'pipeline', 'scale'])
            
        # --- 7. Hireability Score ---
        signals = row.get('redrob_signals', {})
        open_to_work = 1.0 if signals.get('open_to_work_flag', False) else 0.0
        notice = signals.get('notice_period_days', 60)
        notice_score = max(0, (60 - notice) / 60.0) # higher is better
        resp_rate = signals.get('recruiter_response_rate', 0.0)
        interview_comp = signals.get('interview_completion_rate', 0.5)
        offer_acc = signals.get('offer_acceptance_rate', 0.5)
        
        last_active = signals.get('last_active_date', '2026-01-01')
        try:
            days_inactive = (today - datetime.strptime(last_active, '%Y-%m-%d')).days
        except:
            days_inactive = 30
        recency_score = np.exp(-0.05 * max(0, days_inactive))
        
        features.at[idx, 'hireability_score'] = (open_to_work * 2) + notice_score + (resp_rate * 2) + interview_comp + offer_acc + recency_score
        
        # --- 8. Career Consistency Score ---
        # Look for massive contradictions. e.g. headline says "AI Engineer" but no AI skills or career history.
        full_text = headline + summary + current_job_text + past_jobs_text
        ai_mentions = _score_keywords([(full_text, 1.0)], ['ai', 'machine learning', 'ml', 'data'])
        if 'ai' in headline.lower() and ai_mentions < 2:
            features.at[idx, 'career_consistency_score'] = -5.0
        else:
            features.at[idx, 'career_consistency_score'] = 1.0
            
        # --- 9. Timeline Consistency Score ---
        stated_years = row.get('years_of_experience', 0) or 0
        total_months = sum(job.get('duration_months', 0) for job in career)
        calculated_years = total_months / 12.0
        
        if calculated_years > stated_years + 3:
            features.at[idx, 'timeline_consistency_score'] = -5.0 # Impossible timeline
        elif stated_years > calculated_years + 5:
            features.at[idx, 'timeline_consistency_score'] = -3.0 # Ghost experience
        else:
            features.at[idx, 'timeline_consistency_score'] = 1.0
            
        # --- 10. Recruiter Interest Score ---
        saved = signals.get('saved_by_recruiters_30d', 0)
        views = signals.get('profile_views_received_30d', 0)
        search = signals.get('search_appearance_30d', 0)
        features.at[idx, 'recruiter_interest_score'] = (saved * 3) + (views * 0.1) + (search * 0.05)
        
        # --- 11. Startup Readiness Score ---
        features.at[idx, 'startup_readiness_score'] = _score_keywords(text_blocks,
            ['startup', 'early stage', '0 to 1', '0->1', 'founding', 'built from scratch', 'cross-functional', 'wear many hats', 'ownership'])
            
        # --- 12. Leadership Score ---
        features.at[idx, 'leadership_score'] = _score_keywords(text_blocks,
            ['led', 'managed', 'mentored', 'hired', 'owned', 'architected'])
            
        # --- 13. Product Ownership Score ---
        features.at[idx, 'product_ownership_score'] = _score_keywords(text_blocks,
            ['launched', 'shipped', 'customer impact', 'product metrics', 'adoption', 'engagement'])
            
        # --- 14. Synthetic Risk Score (Soft Penalty) ---
        llm_isms = ['delve', 'tapestry', 'synthesized cross-functional', 'spearheaded', 'navigate the landscape']
        features.at[idx, 'synthetic_risk_score'] = sum(1 for w in llm_isms if w in full_text.lower())
        
        # --- 15. Role Progression Score ---
        seniority_map = {'junior': 1, 'associate': 1, 'mid': 2, 'senior': 3, 'lead': 4, 'principal': 5, 'manager': 5, 'director': 6}
        progression = []
        for job in reversed(career):
            t = job.get('title', '').lower()
            level = 2
            for k, v in seniority_map.items():
                if k in t:
                    level = v
                    break
            progression.append(level)
            
        if len(progression) > 1:
            slope = (progression[-1] - progression[0]) / len(progression)
            features.at[idx, 'role_progression_score'] = slope
        else:
            features.at[idx, 'role_progression_score'] = 0.0
            
        # --- 16. JD Disqualifier Penalties ---
        res_penalty = 0.0
        if 'research' in current_job_text and 'production' not in current_job_text:
            res_penalty -= 2.0
            
        lc_penalty = 0.0
        if 'langchain' in current_job_text and 'pytorch' not in full_text and 'tensorflow' not in full_text:
            lc_penalty -= 2.0
            
        features.at[idx, 'jd_disqualifier_penalty'] = res_penalty + lc_penalty
        
        # Other useful bases
        features.at[idx, 'github_activity_score'] = signals.get('github_activity_score', 0)
        
    return features

def get_lexical_scores(query, corpus_texts):
    """
    Fast BM25 approximation using TF-IDF.
    """
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
    tfidf_matrix = vectorizer.fit_transform(corpus_texts + [query])
    query_vec = tfidf_matrix[-1]
    corpus_vecs = tfidf_matrix[:-1]
    scores = corpus_vecs.dot(query_vec.T).toarray().flatten()
    return scores
