import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def extract_recruiter_features(df, jd_data=None):
    """
    Extracts dynamic JD-relative features and universal candidate quality features.
    jd_data expects:
    {
        'keywords': list of core keywords,
        'title_terms': list of target title synonyms,
        'req_skills': list of required skills,
        'seniority_years': target years of experience
    }
    """
    features = pd.DataFrame(index=df.index)

    # If jd_data is not provided, default to the competition Search Engineer constraints
    if jd_data is None:
        jd_data = {
            'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
            'title_terms': ['search', 'machine learning', 'ai', 'ml', 'data scientist', 'backend', 'nlp', 'retrieval', 'ranking'],
            'req_skills': ['python', 'elasticsearch', 'faiss', 'machine learning'],
            'seniority_years': 5
        }

    for idx, row in df.iterrows():
        # Compile text corpus for the candidate
        skills_list = row.get('skills', []) or []
        s_text = " ".join([(s.get('name', '') or '').lower() for s in skills_list if isinstance(s, dict)])
        
        career = row.get('career_history', []) or []
        current_job_text = ""
        current_title = ""
        if career:
            current_job_text = (career[0].get('description', '') or '').lower()
            current_title = (career[0].get('title', '') or '').lower()
            
        full_text = s_text + " " + current_job_text

        # ---------------------------------------------
        # BUCKET A: Query-Relative Features
        # ---------------------------------------------
        
        # 1. Semantic Sim & BM25 Approximation (Keyword Density Overlap)
        hits = sum(1 for k in jd_data['keywords'] if k in full_text)
        features.at[idx, 'semantic_sim'] = hits / max(len(jd_data['keywords']), 1)
        features.at[idx, 'bm25_score'] = features.at[idx, 'semantic_sim'] * 0.8  # Proxy since real BM25 is offline
        
        # 2. Title Similarity
        t_hits = sum(1 for w in jd_data['title_terms'] if w in current_title)
        features.at[idx, 'title_similarity'] = min(t_hits / 2.0, 1.0)
        
        # 3. Skill Coverage
        sk_hits = sum(1 for k in jd_data['req_skills'] if k in s_text)
        features.at[idx, 'skill_coverage'] = sk_hits / max(len(jd_data['req_skills']), 1)
        
        # 4. Seniority Alignment
        total_months = sum((job.get('duration_months', 0) or 0) for job in career)
        yoe = total_months / 12.0
        diff = abs(yoe - jd_data['seniority_years'])
        features.at[idx, 'seniority_alignment'] = max(0, 1.0 - (diff / 10.0))
        
        # 5. Keyword Trap Penalty
        if features.at[idx, 'bm25_score'] > 0.6 and features.at[idx, 'title_similarity'] == 0:
            features.at[idx, 'keyword_trap_penalty'] = 1.0
        else:
            features.at[idx, 'keyword_trap_penalty'] = 0.0

        # ---------------------------------------------
        # BUCKET B: Universal Candidate Quality
        # ---------------------------------------------
        signals = row.get('redrob_signals', {}) or {}
        
        q = 0.0
        q += (signals.get('profile_completeness_score', 50) / 100.0)
        q += min((signals.get('github_activity_score', 0) / 100.0), 1.0)
        if signals.get('verified_email'): q += 0.5
        if signals.get('linkedin_connected'): q += 0.5
        
        features.at[idx, 'quality_score'] = q
        
        # Metadata
        features.at[idx, 'current_title'] = current_title
        features.at[idx, 'years_of_experience'] = yoe

    return features

# Used for extraction logic
FEATURE_COLS = [
    'semantic_sim', 'bm25_score', 'title_similarity', 
    'skill_coverage', 'seniority_alignment', 'quality_score', 'keyword_trap_penalty'
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
