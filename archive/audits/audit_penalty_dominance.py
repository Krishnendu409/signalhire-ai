import json
import pandas as pd
import numpy as np
from hackathon_pipeline.engine import RankingEngine

print("Loading engine...")
engine = RankingEngine()

search_jd = {
    "family": "Search Engineer",
    "title_terms": ["search", "engineer", "relevance", "ranking", "retrieval", "nlp", "machine learning"],
    "req_skills": ["python", "elasticsearch", "faiss", "machine learning", "nlp", "deep learning", "pytorch"],
    "keywords": ["search", "relevance", "ranking", "retrieval", "nlp", "machine learning", "ai", "data science"]
}

print("Running baseline...")
feat_base = engine._extract_features(search_jd)
ranked_base = engine._rank_features(feat_base.copy())
top100_base = ranked_base.head(100)['candidate_id'].tolist()
recall_base = len(ranked_base[ranked_base['final_score'] > 0])

results = []

def run_penalty_test(scenario, penalty_val):
    print(f"Running {scenario}...")
    engine.config['weights']['consistency_penalty'] = penalty_val
    ranked = engine._rank_features(feat_base.copy())
    top100 = ranked.head(100)['candidate_id'].tolist()
    overlap = len(set(top100_base).intersection(set(top100)))
    recall = len(ranked[ranked['final_score'] > 0])
    honeypots = ranked.head(100)['is_trap'].sum()
    
    # rank shift
    # how much did candidates in the original top 100 move?
    orig_ranks = pd.Series(np.arange(1, 101), index=top100_base)
    new_ranks = pd.Series(np.arange(1, len(ranked)+1), index=ranked['candidate_id'])
    
    shifts = []
    for cid in top100_base:
        if cid in new_ranks:
            shifts.append(abs(orig_ranks[cid] - new_ranks[cid]))
            
    avg_shift = np.mean(shifts) if shifts else 0
    
    results.append({
        "Scenario": scenario,
        "Penalty Value": penalty_val,
        "Top 100 Overlap": overlap,
        "Recall (>0 score)": recall,
        "Avg Rank Shift (Orig Top 100)": avg_shift,
        "Honeypots in Top 100": int(honeypots)
    })

run_penalty_test("Baseline", -2.00)
run_penalty_test("Disabled", 0.00)
run_penalty_test("Reduced 50%", -1.00)
run_penalty_test("Increased 50%", -3.00)

df_res = pd.DataFrame(results)
print(df_res.to_markdown(index=False))
df_res.to_csv('penalty_dominance_results.csv', index=False)
print("Saved to penalty_dominance_results.csv")
