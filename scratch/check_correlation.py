import pandas as pd
import numpy as np

def run_correlation_check():
    import sys
    sys.path.append(r"C:\Users\krish\Documents\signalhire")
    print("Loading training data to check pseudo-label correlations...")
    # We need to recreate the features_df from train_lightgbm logic quickly
    from hackathon_pipeline.train_lightgbm import generate_training_data
    
    # We will sample 2000 just for speed
    input_file = r"C:\Users\krish\Documents\signalhire\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
    df = generate_training_data(input_file, num_samples=2000)
    
    # Calculate correlations
    labels = df['label']
    print("\n--- Pearson Correlation with Pseudo-Label ---")
    for col in df.columns:
        if col not in ['label', 'raw_final_score', 'candidate_id', 'profile']:
            try:
                corr = labels.corr(df[col])
                if pd.notna(corr) and abs(corr) > 0.05:
                    print(f"{col:<30} | {corr:.4f}")
            except Exception as e:
                pass

if __name__ == "__main__":
    run_correlation_check()
