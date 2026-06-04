import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer

def calculate_fraud_risk(df):
    """
    Implements dataset forensics to detect honeypots and fraudulent profiles.
    Returns the dataframe with a 'fraud_risk_score' column.
    """
    df = df.copy()
    fraud_scores = np.zeros(len(df))
    
    # Example Trap 1: Impossible career duration
    # If the sum of all job durations greatly exceeds stated years of experience
    if 'years_of_experience' in df.columns and 'career_history' in df.columns:
        for idx, row in df.iterrows():
            total_months = 0
            if isinstance(row['career_history'], list):
                for job in row['career_history']:
                    # Assuming format has start_date and end_date (or duration_months)
                    duration = job.get('duration_months', 0)
                    total_months += duration
            
            stated_years = row.get('years_of_experience', 0) or 0
            if total_months / 12 > stated_years + 2:  # 2 years variance buffer
                fraud_scores[idx] += 1.0
                
    # Example Trap 2: Keyword stuffers
    if 'skills' in df.columns and 'redrob_signals' in df.columns:
        for idx, row in df.iterrows():
            signals = row.get('redrob_signals', {})
            endorsements = signals.get('endorsements_received', 0)
            skills = row.get('skills', [])
            
            expert_count = sum(1 for s in skills if s.get('proficiency') == 'Expert')
            if expert_count > 50 and endorsements < 5:
                fraud_scores[idx] += 1.0
                
    df['fraud_risk_score'] = fraud_scores
    return df

def extract_behavioral_features(df):
    """
    Extracts tabular features from nested JSON and redrob_signals for LightGBM.
    """
    df = df.copy()
    
    features = pd.DataFrame(index=df.index)
    
    # Default to today if parsing fails
    today = datetime(2026, 1, 1) # Static reference for hackathon consistency
    
    for idx, row in df.iterrows():
        signals = row.get('redrob_signals', {})
        
        # 1. Recency Decay Score (Lambda = 0.05)
        last_active = signals.get('last_active_date', '2026-01-01')
        try:
            days_inactive = (today - datetime.strptime(last_active, '%Y-%m-%d')).days
        except:
            days_inactive = 0
        days_inactive = max(0, days_inactive)
        features.at[idx, 'recency_decay_score'] = np.exp(-0.05 * days_inactive)
        
        # 2. Avg Tenure Months
        career = row.get('career_history', [])
        if len(career) > 0:
            total_months = sum(job.get('duration_months', 12) for job in career)
            features.at[idx, 'avg_tenure_months'] = total_months / len(career)
        else:
            features.at[idx, 'avg_tenure_months'] = 0
            
        # 3. Product Company Proxy (Simplistic check for 'product' vs 'services/consulting' in career text)
        career_text = " ".join([job.get('description', '').lower() for job in career])
        product_count = career_text.count('product') + career_text.count('startup')
        consulting_count = career_text.count('consulting') + career_text.count('services') + career_text.count('agency')
        
        total = product_count + consulting_count
        features.at[idx, 'product_company_ratio'] = product_count / total if total > 0 else 0.5
        
        # Other signals
        features.at[idx, 'recruiter_response_rate'] = signals.get('recruiter_response_rate', 0.5)
        features.at[idx, 'github_activity_score'] = signals.get('github_activity_score', 0)
        features.at[idx, 'notice_period_days'] = signals.get('notice_period_days', 30)
        
    return features

def get_lexical_scores(query, corpus_texts):
    """
    Fast BM25 approximation using TF-IDF.
    Returns an array of scores.
    """
    vectorizer = TfidfVectorizer(stop_words='english')
    # Fit on corpus + query to ensure vocab aligns
    tfidf_matrix = vectorizer.fit_transform(corpus_texts + [query])
    
    # Query is the last element
    query_vec = tfidf_matrix[-1]
    corpus_vecs = tfidf_matrix[:-1]
    
    # Dot product for fast similarity
    scores = corpus_vecs.dot(query_vec.T).toarray().flatten()
    return scores
