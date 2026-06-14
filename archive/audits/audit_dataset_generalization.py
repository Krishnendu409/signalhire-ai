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

# The dataset generalization test:
# Remove top companies, remove dominant title families, stratified samples, reduced datasets.
# Wait, "top companies" - my engine doesn't even extract companies in `engine.py`. `self.df` only uses current_title, skills_text, desc_text, quality_score.
# So removing top companies won't change the ranking *function*, but it changes the *dataset* distribution.
# I will simulate different dataset cuts.

# Full Baseline
feat_full = engine._extract_features(search_jd)
ranked_full = engine._rank_features(feat_full)
top100_full = ranked_full.head(100)['candidate_id'].tolist()

results = []

def run_dataset_cut(name, mask):
    print(f"Running subset: {name} (Size: {mask.sum()})")
    
    # Apply mask
    feat_cut = feat_full[mask].copy()
    ranked = engine._rank_features(feat_cut)
    top100 = ranked.head(100)['candidate_id'].tolist()
    
    overlap = len(set(top100_full).intersection(set(top100)))
    recall = len(ranked[ranked['final_score'] > 0])
    honeypots = ranked.head(100)['is_trap'].sum()
    
    # Diversity: unique titles in top 100
    diversity = ranked.head(100)['current_title'].nunique()
    
    results.append({
        "Dataset Cut": name,
        "Size": mask.sum(),
        "Top 100 Overlap (w/ Full)": overlap,
        "Recall": recall,
        "Honeypots in Top 100": int(honeypots),
        "Title Diversity (Top 100)": diversity
    })

# 1. Remove dominant title families (Remove all engineers and managers)
mask_no_dominant = ~feat_full['current_title'].str.contains('engineer|manager|developer|director', regex=True, na=False)
run_dataset_cut("Removed Dominant Titles", mask_no_dominant)

# 2. Stratified sample (10%)
# For reproducibility
np.random.seed(42)
mask_10_percent = np.random.rand(len(feat_full)) < 0.1
run_dataset_cut("Random 10% Sample", mask_10_percent)

# 3. Stratified sample (50%)
mask_50_percent = np.random.rand(len(feat_full)) < 0.5
run_dataset_cut("Random 50% Sample", mask_50_percent)

df_res = pd.DataFrame(results)
print(df_res.to_markdown(index=False))
df_res.to_csv('dataset_generalization_results.csv', index=False)
print("Saved to dataset_generalization_results.csv")
