import json
import pandas as pd
import numpy as np
import lightgbm as lgb
from feature_extractor import extract_recruiter_features, FEATURE_COLS


def generate_training_data(input_path, num_samples=10000):
    """
    Load candidates and generate pseudo-labels using our handcrafted recruiter score.
    Uses 10k samples (up from 2k) for better feature variance.
    """
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

    # Simulate semantic_sim and bm25_score (query-dependent at runtime)
    np.random.seed(42)
    features_df['semantic_sim'] = np.random.uniform(0.3, 1.0, size=len(features_df))
    features_df['bm25_score'] = np.random.uniform(0.0, 1.0, size=len(features_df))

    # Generate Handcrafted Recruiter Score as Pseudo-Label
    labels = np.zeros(len(features_df))
    for i, (idx, row) in enumerate(features_df.iterrows()):
        # Core JD alignment (highest weight)
        core = (
            row['retrieval_experience_score'] * 2.5 +
            row['ranking_experience_score'] * 2.5 +
            row['embedding_experience_score'] * 2.0 +
            row['vector_db_score'] * 2.0 +
            row['evaluation_framework_score'] * 2.0 +
            row['production_ml_score'] * 1.5
        )

        # Soft skills & reliability
        soft = (
            row['startup_readiness_score'] * 1.0 +
            row['leadership_score'] * 1.0 +
            row['product_ownership_score'] * 1.0 +
            row['hireability_score'] * 1.5 +
            row['recruiter_interest_score'] * 0.5 +
            row['role_progression_score'] * 0.8
        )

        # Trust & profile quality
        trust = (
            row['profile_completeness'] * 1.0 +
            row['avg_skill_assessment'] * 1.5 +
            row['trust_score'] * 0.5 +
            row['github_activity_score'] * 1.0
        )

        # Consistency & penalties (can go negative)
        penalties = (
            row['career_consistency_score'] * 2.0 +
            row['timeline_consistency_score'] * 1.5 +
            row['jd_disqualifier_penalty'] * 1.0 -
            row['synthetic_risk_score'] * 0.3
        )

        # Query-dependent (simulated)
        query = row['semantic_sim'] * 3.0 + row['bm25_score'] * 1.5

        final_score = core + soft + trust + penalties + query

        # Map to 0–4 integer labels for LambdaRank
        normalized = max(0, min(4, final_score / 8.0))
        labels[i] = int(round(normalized))

    features_df['label'] = labels.astype(int)

    # Print label distribution
    unique, counts = np.unique(labels, return_counts=True)
    print("Label distribution:")
    for u, c in zip(unique, counts):
        print(f"  Label {int(u)}: {c} candidates")

    return features_df


def train_lambdarank(df, output_model_path):
    print("Training LightGBM LambdaRank model...")

    X = df[FEATURE_COLS]
    y = df['label']

    # Single group (all candidates ranked against one query)
    group = [len(X)]

    train_data = lgb.Dataset(X, label=y, group=group)

    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_eval_at': [10, 100],
        'learning_rate': 0.05,
        'num_leaves': 63,
        'min_data_in_leaf': 10,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbosity': -1,
        'random_state': 42
    }

    print("Fitting model...")
    model = lgb.train(params, train_data, num_boost_round=200)

    print(f"Saving model to {output_model_path}")
    model.save_model(output_model_path)

    importance = model.feature_importance(importance_type='gain')
    print("\nFeature Importances (Gain):")
    for name, imp in sorted(zip(FEATURE_COLS, importance), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {imp:.2f}")

    # Check for zero-importance features
    zero_feats = [n for n, i in zip(FEATURE_COLS, importance) if i == 0]
    if zero_feats:
        print(f"\n⚠️  WARNING: {len(zero_feats)} features have zero importance: {zero_feats}")


if __name__ == "__main__":
    import os
    input_file = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(input_file):
        input_file = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"

    df = generate_training_data(input_file)
    train_lambdarank(df, "lgbm_ranker.txt")
