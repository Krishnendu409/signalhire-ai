import json
import pandas as pd
import numpy as np
import lightgbm as lgb
from feature_extractor import calculate_fraud_risk, extract_behavioral_features

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
    df = calculate_fraud_risk(df)
    features_df = extract_behavioral_features(df)
    
    # We simulate semantic similarity as a random normal distribution for training purposes,
    # as the real similarity will depend on the dynamic query. 
    # In reality, we'd train on (candidate, query) pairs. Since we don't have labeled queries,
    # we generate a robust pseudo-labeled dataset teaching the model how to weight behavioral signals.
    np.random.seed(42)
    features_df['semantic_sim'] = np.random.uniform(0.3, 1.0, size=len(features_df))
    features_df['bm25_score'] = np.random.uniform(0.0, 1.0, size=len(features_df))
    
    # Include fraud score
    features_df['fraud_risk_score'] = df['fraud_risk_score']
    
    # Generate Pseudo-Labels (0 to 4)
    labels = np.zeros(len(features_df))
    for idx, row in features_df.iterrows():
        # Immediate disqualifiers
        if row['fraud_risk_score'] >= 1.0 or row['notice_period_days'] > 60:
            labels[idx] = 0
            continue
            
        score = 0
        
        # Technical fit proxies
        if row['semantic_sim'] > 0.8 and row['bm25_score'] > 0.5:
            score += 2
        elif row['semantic_sim'] > 0.6:
            score += 1
            
        # Behavioral fit
        if row['recency_decay_score'] > 0.8 and row['recruiter_response_rate'] > 0.7:
            score += 1
        
        # Experience multiplier
        if 24 <= row['avg_tenure_months'] <= 60 and row['product_company_ratio'] > 0.5:
            score += 1
            
        labels[idx] = min(4, score)
        
    features_df['label'] = labels
    return features_df

def train_lambdarank(df, output_model_path):
    print("Training LightGBM LambdaRank model...")
    
    # Features for the model
    feature_cols = [
        'semantic_sim', 'bm25_score', 'recency_decay_score', 
        'avg_tenure_months', 'product_company_ratio', 
        'recruiter_response_rate', 'github_activity_score', 
        'notice_period_days', 'fraud_risk_score'
    ]
    
    X = df[feature_cols]
    y = df['label']
    
    # LambdaRank requires query groups. 
    # Since we are training to optimize a single list for a generic query, we set all data to one group.
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
    
    # Print feature importance
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
