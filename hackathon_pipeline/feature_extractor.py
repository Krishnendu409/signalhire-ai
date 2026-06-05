import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
import re


def _score_keywords_bounded(text_blocks, keywords):
    """
    Weighted keyword scoring with word-boundary matching to prevent double-counting.
    text_blocks: list of (text, weight) tuples
    keywords: list of strings, checked longest-first to avoid substring overlaps
    """
    score = 0.0
    # Sort keywords longest-first so "semantic search" is checked before "search"
    sorted_kw = sorted(keywords, key=len, reverse=True)
    for text, weight in text_blocks:
        if not text:
            continue
        t = text.lower()
        matched_spans = []
        for kw in sorted_kw:
            kw_lower = kw.lower()
            # Use word boundary regex to avoid partial matches
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            for m in re.finditer(pattern, t):
                # Check this span doesn't overlap with an already-matched span
                start, end = m.start(), m.end()
                if not any(start < me and end > ms for ms, me in matched_spans):
                    score += weight
                    matched_spans.append((start, end))
    return min(score, 10.0)  # Cap at 10 to prevent any single feature from dominating


def _flatten_candidate(row):
    """
    Extract fields from the nested 'profile' dict into top-level access.
    The candidate schema nests headline, summary, years_of_experience, etc.
    inside a 'profile' object.
    """
    profile = row.get('profile', {}) or {}
    return {
        'headline': profile.get('headline', '') or '',
        'summary': profile.get('summary', '') or '',
        'years_of_experience': profile.get('years_of_experience', 0) or 0,
        'current_title': profile.get('current_title', '') or '',
        'current_company': profile.get('current_company', '') or '',
        'current_company_size': profile.get('current_company_size', '') or '',
        'current_industry': profile.get('current_industry', '') or '',
        'location': profile.get('location', '') or '',
        'country': profile.get('country', '') or '',
    }


def extract_recruiter_features(df):
    """
    Complete feature engineering based on recruiter logic and JD requirements.
    Handles the nested 'profile' structure correctly.
    """
    df = df.copy()
    features = pd.DataFrame(index=df.index)
    today = datetime(2026, 6, 1)

    for idx, row in df.iterrows():
        # --- FLATTEN PROFILE ---
        flat = _flatten_candidate(row)
        headline = flat['headline']
        summary = flat['summary']
        years_exp = flat['years_of_experience']
        current_title = flat['current_title']
        company_size = flat['current_company_size']

        skills_list = row.get('skills', []) or []
        skills_text = " ".join([s.get('name', '') for s in skills_list])

        career = row.get('career_history', []) or []
        signals = row.get('redrob_signals', {}) or {}

        # --- PREPARE TEXT BLOCKS FOR WEIGHTED SCORING ---
        # current job = first entry in career_history (most recent)
        current_job_text = ""
        past_jobs_text = ""
        if career:
            current_job_text = (
                (career[0].get('title', '') or '') + " " +
                (career[0].get('description', '') or '')
            ).lower()
            if len(career) > 1:
                past_jobs_text = " ".join([
                    ((j.get('title', '') or '') + " " + (j.get('description', '') or ''))
                    for j in career[1:]
                ]).lower()

        # Weights: Headline/Summary (1.5), Current Job (2.0), Past Jobs (0.8), Skills (1.0)
        text_blocks = [
            (headline + " " + summary, 1.5),
            (current_job_text, 2.0),
            (past_jobs_text, 0.8),
            (skills_text, 1.0)
        ]

        full_text = (headline + " " + summary + " " + current_job_text + " " + past_jobs_text + " " + skills_text).lower()

        # =============================================
        # TIER 1: JD-Specific Technical Alignment
        # =============================================

        # 1. Retrieval Experience Score
        features.at[idx, 'retrieval_experience_score'] = _score_keywords_bounded(text_blocks, [
            'retrieval', 'semantic search', 'information retrieval',
            'search engine', 'search system', 'query understanding',
            'candidate matching', 'document retrieval'
        ])

        # 2. Ranking Experience Score
        features.at[idx, 'ranking_experience_score'] = _score_keywords_bounded(text_blocks, [
            'ranking', 'learning to rank', 'learning-to-rank',
            'recommendation system', 'recommender', 'lambdamart',
            'xgboost ranker', 'search ranking', 'candidate ranking',
            'relevance', 'reranking', 're-ranking'
        ])

        # 3. Embedding Experience Score
        features.at[idx, 'embedding_experience_score'] = _score_keywords_bounded(text_blocks, [
            'embedding', 'sentence transformer', 'sentence-transformers',
            'bge', 'e5', 'vectorization', 'semantic similarity',
            'word2vec', 'bert', 'text embedding'
        ])

        # 4. Vector DB Score
        features.at[idx, 'vector_db_score'] = _score_keywords_bounded(text_blocks, [
            'pinecone', 'qdrant', 'milvus', 'weaviate', 'faiss',
            'elasticsearch', 'opensearch', 'vector database',
            'vector store', 'chromadb', 'annoy', 'hnsw'
        ])

        # 5. Evaluation Framework Score
        features.at[idx, 'evaluation_framework_score'] = _score_keywords_bounded(text_blocks, [
            'ndcg', 'mrr', 'mean reciprocal rank', 'map',
            'mean average precision', 'a/b testing', 'ab testing',
            'ranking evaluation', 'precision at k', 'recall at k',
            'offline evaluation', 'online evaluation'
        ])

        # 6. Production ML Score
        features.at[idx, 'production_ml_score'] = _score_keywords_bounded(text_blocks, [
            'deployed', 'production', 'serving', 'inference',
            'monitoring', 'mlops', 'ci/cd', 'docker', 'kubernetes',
            'aws sagemaker', 'ml pipeline', 'model serving',
            'latency', 'throughput', 'scalab'
        ])

        # =============================================
        # TIER 1: Hireability & Behavioral Signals
        # =============================================

        # 7. Hireability Score (composite from redrob_signals)
        open_to_work = 1.0 if signals.get('open_to_work_flag', False) else 0.0
        notice = signals.get('notice_period_days', 90) or 90
        notice_score = max(0, (90 - notice) / 90.0)
        resp_rate = signals.get('recruiter_response_rate', 0.0) or 0.0
        resp_time = signals.get('avg_response_time_hours', 168) or 168
        resp_time_score = max(0, (168 - resp_time) / 168.0)
        interview_comp = signals.get('interview_completion_rate', 0.5) or 0.5
        offer_acc_raw = signals.get('offer_acceptance_rate', -1)
        offer_acc = offer_acc_raw if offer_acc_raw >= 0 else 0.5

        last_active = signals.get('last_active_date', '2025-01-01') or '2025-01-01'
        try:
            days_inactive = (today - datetime.strptime(last_active, '%Y-%m-%d')).days
        except Exception:
            days_inactive = 60
        recency_score = np.exp(-0.03 * max(0, days_inactive))

        features.at[idx, 'hireability_score'] = (
            open_to_work * 1.5 +
            notice_score * 1.5 +
            resp_rate * 2.0 +
            resp_time_score * 1.0 +
            interview_comp * 1.0 +
            offer_acc * 1.0 +
            recency_score * 1.5
        )

        # 8. Career Consistency Score (cross-field text similarity)
        headline_tokens = set(re.findall(r'[a-z]{3,}', headline.lower()))
        career_tokens = set(re.findall(r'[a-z]{3,}', (current_job_text + " " + past_jobs_text)))
        summary_tokens = set(re.findall(r'[a-z]{3,}', summary.lower()))
        all_career_tokens = career_tokens | summary_tokens
        if headline_tokens and all_career_tokens:
            overlap = len(headline_tokens & all_career_tokens)
            consistency = overlap / max(len(headline_tokens), 1)
        else:
            consistency = 0.5
        features.at[idx, 'career_consistency_score'] = consistency

        # 9. Timeline Consistency Score (soft, continuous)
        stated_years = years_exp
        total_months = sum((job.get('duration_months', 0) or 0) for job in career)
        calculated_years = total_months / 12.0
        gap = abs(stated_years - calculated_years)
        if gap <= 2:
            features.at[idx, 'timeline_consistency_score'] = 1.0
        elif gap <= 5:
            features.at[idx, 'timeline_consistency_score'] = 0.5
        elif gap <= 10:
            features.at[idx, 'timeline_consistency_score'] = 0.0
        else:
            features.at[idx, 'timeline_consistency_score'] = -1.0

        # 10. Recruiter Interest Score
        saved = signals.get('saved_by_recruiters_30d', 0) or 0
        views = signals.get('profile_views_received_30d', 0) or 0
        search_app = signals.get('search_appearance_30d', 0) or 0
        features.at[idx, 'recruiter_interest_score'] = (
            min(saved * 2.0, 10.0) +
            min(views * 0.1, 5.0) +
            min(search_app * 0.02, 3.0)
        )

        # =============================================
        # TIER 2: Soft Skills & Readiness
        # =============================================

        # 11. Startup Readiness Score
        features.at[idx, 'startup_readiness_score'] = _score_keywords_bounded(text_blocks, [
            'startup', 'early stage', 'early-stage', 'founding',
            'built from scratch', 'cross-functional', 'wore many hats',
            'ownership', 'greenfield', 'zero to one', '0 to 1'
        ])
        # Also boost if company_size is small
        small_co = company_size in ['1-10', '11-50', '51-200']
        if small_co:
            features.at[idx, 'startup_readiness_score'] += 1.5

        # 12. Leadership Score
        features.at[idx, 'leadership_score'] = _score_keywords_bounded(text_blocks, [
            'led', 'managed', 'mentored', 'hired', 'architected',
            'team lead', 'tech lead', 'engineering manager',
            'built the team', 'grew the team'
        ])

        # 13. Product Ownership Score
        features.at[idx, 'product_ownership_score'] = _score_keywords_bounded(text_blocks, [
            'launched', 'shipped', 'customer impact',
            'product metrics', 'adoption', 'engagement',
            'owned end-to-end', 'drove', 'increased revenue',
            'reduced churn', 'improved retention'
        ])

        # =============================================
        # TIER 3: Fraud / Authenticity
        # =============================================

        # 14. Synthetic Risk Score (soft penalty, low weight)
        llm_patterns = [
            'delve into', 'tapestry', 'navigate the landscape',
            'orchestrated synergies', 'holistic approach',
            'cutting-edge solutions', 'paradigm shift'
        ]
        synth_count = sum(1 for w in llm_patterns if w in full_text)
        features.at[idx, 'synthetic_risk_score'] = min(synth_count, 5)

        # 15. Role Progression Score
        seniority_map = {
            'intern': 0, 'junior': 1, 'associate': 1.5,
            'mid': 2, 'senior': 3, 'staff': 4,
            'lead': 4, 'principal': 5, 'manager': 4.5,
            'director': 6, 'vp': 7, 'cto': 8
        }
        progression = []
        for job in reversed(career):
            t = (job.get('title', '') or '').lower()
            level = 2  # default mid-level
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

        # 16. JD Disqualifier Penalties (soft)
        penalty = 0.0
        if 'research' in current_job_text and 'production' not in current_job_text and 'deploy' not in current_job_text:
            penalty -= 1.0
        if 'langchain' in full_text and 'pytorch' not in full_text and 'tensorflow' not in full_text and 'model' not in current_job_text:
            penalty -= 1.0
        features.at[idx, 'jd_disqualifier_penalty'] = penalty

        # =============================================
        # NEW: Previously Unused redrob_signals
        # =============================================

        # 17. Profile Completeness
        features.at[idx, 'profile_completeness'] = (signals.get('profile_completeness_score', 50) or 50) / 100.0

        # 18. Skill Assessment Score (mean of actual tested scores)
        assessments = signals.get('skill_assessment_scores', {}) or {}
        if assessments:
            features.at[idx, 'avg_skill_assessment'] = np.mean(list(assessments.values())) / 100.0
        else:
            features.at[idx, 'avg_skill_assessment'] = 0.0

        # 19. Trust / Verification Score
        verified_email = 1.0 if signals.get('verified_email', False) else 0.0
        verified_phone = 1.0 if signals.get('verified_phone', False) else 0.0
        linkedin = 1.0 if signals.get('linkedin_connected', False) else 0.0
        features.at[idx, 'trust_score'] = verified_email + verified_phone + linkedin

        # 20. GitHub Activity
        gh = signals.get('github_activity_score', -1)
        features.at[idx, 'github_activity_score'] = max(gh, 0) / 100.0

        # 21. Years of experience (for reasoning generation downstream)
        features.at[idx, 'years_of_experience'] = years_exp

        # 22. Current title (for reasoning generation downstream)
        features.at[idx, 'current_title'] = current_title

    return features


# Feature columns used by LightGBM (excludes metadata cols like current_title, years_of_experience)
FEATURE_COLS = [
    'semantic_sim', 'bm25_score',
    'retrieval_experience_score', 'ranking_experience_score', 'embedding_experience_score',
    'vector_db_score', 'evaluation_framework_score', 'production_ml_score',
    'hireability_score', 'career_consistency_score', 'timeline_consistency_score',
    'recruiter_interest_score', 'startup_readiness_score', 'leadership_score',
    'product_ownership_score', 'synthetic_risk_score', 'role_progression_score',
    'jd_disqualifier_penalty', 'github_activity_score',
    'profile_completeness', 'avg_skill_assessment', 'trust_score'
]


def get_lexical_scores(query, corpus_texts):
    """
    Fast BM25 approximation using TF-IDF.
    """
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus_texts + [query])
    query_vec = tfidf_matrix[-1]
    corpus_vecs = tfidf_matrix[:-1]
    scores = corpus_vecs.dot(query_vec.T).toarray().flatten()
    return scores
