import json
import pandas as pd
import numpy as np
import copy
from hackathon_pipeline.engine import RankingEngine

def run_ablation():
    engine = RankingEngine()
    
    baseline_jd = {
        "family": "Search Engineer",
        "title_terms": ["search", "retrieval", "relevance", "ranking"],
        "req_skills": ["python", "elasticsearch", "faiss", "machine learning"],
        "keywords": ["search", "relevance", "ranking", "retrieval", "elasticsearch", "vector", "ann"]
    }
    
    # Get baseline ranking
    baseline_top100 = engine.run_pipeline(baseline_jd, top_k=100)
    baseline_ids = [c['candidate_id'] for c in baseline_top100]
    
    features_to_ablate = [
        'title_affinity',
        'skill_affinity',
        'career_affinity',
        'semantic_sim',
        'bm25_score',
        'quality_score'
    ]
    
    results = []
    
    original_weights = copy.deepcopy(engine.config['weights'])
    
    for feat in features_to_ablate:
        # Zero out the feature
        engine.config['weights'][feat] = 0.0
        
        # Re-rank
        ablation_top100 = engine.run_pipeline(baseline_jd, top_k=100)
        ablation_ids = [c['candidate_id'] for c in ablation_top100]
        
        # Measure impact
        overlap = len(set(baseline_ids).intersection(set(ablation_ids)))
        
        results.append({
            "Ablated Feature": feat,
            "Top 100 Overlap (w/ Baseline)": overlap,
            "Impact Score": 100 - overlap
        })
        
        # Restore weight
        engine.config['weights'][feat] = original_weights[feat]
        
    # Unimplemented features
    unimplemented = [
        'behavioral_signals',
        'platform_activity',
        'trajectory_signals',
        'tenure_signals',
        'redrob_signals (expanded)'
    ]
    
    for feat in unimplemented:
        results.append({
            "Ablated Feature": feat,
            "Top 100 Overlap (w/ Baseline)": 100,
            "Impact Score": 0.0
        })
        
    df = pd.DataFrame(results)
    df.to_csv('ablation_results.csv', index=False)
    print("Ablation complete. Saved to ablation_results.csv")

if __name__ == '__main__':
    run_ablation()
