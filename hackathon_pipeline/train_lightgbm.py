import json
import pandas as pd
import numpy as np
import lightgbm as lgb
from feature_extractor import extract_recruiter_features

def generate_training_data(input_path, num_samples=2000):
    print(f"Loading {num_samples} samples from {input_path} for pseudo-label training...")
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= num_samples:
                break
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                    
    df = pd.DataFrame(records)
    
    print("Extracting features...")
    features_df = extract_recruiter_features(df)
    
    # We simulate semantic similarity and BM25 as they depend on the query dynamically
    np.random.seed(42)
    features_df['semantic_sim'] = np.random.uniform(0.3, 1.0, size=len(features_df))
    features_df['bm25_score'] = np.random.uniform(0.0, 1.0, size=len(features_df))
    
    # Generate Handcrafted Recruiter Score as Pseudo-Label
    labels = np.zeros(len(features_df))
    for idx, row in features_df.iterrows():
        # Core alignment
        core = (
            row['retrieval_experience_score'] * 2.0 +
            row['ranking_experience_score'] * 2.5 +
            row['embedding_experience_score'] * 2.0 +
            row['vector_db_score'] * 1.5 +
            row['evaluation_framework_score'] * 1.5 +
            row['production_ml_score'] * 1.5
        )
        
        # Soft skills & reliability
        soft = (
            row['startup_readiness_score'] * 1.0 +
            row['leadership_score'] * 1.0 +
            row['product_ownership_score'] * 1.0 +
            row['hireability_score'] * 2.0 +
            row['recruiter_interest_score'] * 0.5 + 
            row['role_progression_score'] * 1.0
        )
        
        # Penalties and Consistencies
        penalties = (
            row['career_consistency_score'] + # Negative if inconsistent
            row['timeline_consistency_score'] + # Negative if inconsistent
            row['jd_disqualifier_penalty'] - 
            (row['synthetic_risk_score'] * 0.5)
        )
        
        # Query dependencies (simulated)
        query = (row['semantic_sim'] * 5.0) + (row['bm25_score'] * 2.0)
        
        final_score = core + soft + penalties + query
        
        # Normalize to 0-5 and cast to int for LambdaRank
        labels[idx] = int(round(max(0, min(5, final_score / 5.0))))
        
    features_df['label'] = labels
    return features_df

def train_lambdarank(df, output_model_path):
    print("Training LightGBM LambdaRank model...")
    
    # All features for the model
    feature_cols = [
        'semantic_sim', 'bm25_score',
        'retrieval_experience_score', 'ranking_experience_score', 'embedding_experience_score',
        'vector_db_score', 'evaluation_framework_score', 'production_ml_score',
        'hireability_score', 'career_consistency_score', 'timeline_consistency_score',
        'recruiter_interest_score', 'startup_readiness_score', 'leadership_score',
        'product_ownership_score', 'synthetic_risk_score', 'role_progression_score',
        'jd_disqualifier_penalty', 'github_activity_score'
    ]
    
    X = df[feature_cols]
    y = df['label']
    
    group = [len(X)] 
    
    train_data = lgb.Dataset(X, label=y, group=group)
    
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_eval_at': [10, 100],
        'learning_rate': 0.05,
        'num_leaves': 31,
        'min_data_in_leaf': 20,
        'verbosity': -1,
        'random_state': 42
    }
    
    print("Fitting model...")
    model = lgb.train(params, train_data, num_boost_round=100)
    
    print(f"Saving model to {output_model_path}")
    model.save_model(output_model_path)
    
    importance = model.feature_importance(importance_type='gain')
    print("\nFeature Importances (Gain):")
    for name, imp in sorted(zip(feature_cols, importance), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {imp:.2f}")

if __name__ == "__main__":
    import os
    input_file = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(input_file):
        input_file = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
        
    df = generate_training_data(input_file)
    train_lambdarank(df, "lgbm_ranker.txt")
