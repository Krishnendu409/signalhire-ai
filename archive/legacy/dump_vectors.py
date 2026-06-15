import json
import pandas as pd
from hackathon_pipeline.engine import RankingEngine

engine = RankingEngine()
jd = {
    "family": "Search Engineer",
    "title_terms": ["search", "retrieval", "relevance", "ranking", "nlp", "machine learning", "ai", "data scientist", "ml"],
    "req_skills": ["python", "elasticsearch", "faiss", "machine learning", "nlp", "deep learning", "pytorch", "tensorflow", "scikit-learn"],
    "keywords": ["search", "vector", "embedding", "llm"],
    "min_experience": 5,
    "max_experience": 15,
    "budget_lpa_max": 999.0,
    "work_mode": "remote",
    "required_certifications": [],
    "degree_required": ""
}

# Run 1
feat_base1 = engine._extract_features(jd)
ranked1 = engine._rank_features(feat_base1).head(20)

# Run 2
feat_base2 = engine._extract_features(jd)
ranked2 = engine._rank_features(feat_base2).head(20)

# Dump output to file
with open('VERIFICATION_DUMP.md', 'w') as f:
    f.write("# 6. Feature Vector Dump (Top 20)\n\n")
    f.write("```csv\n")
    cols = [
        'candidate_id', 'current_title', 'title_affinity', 'skill_affinity', 
        'career_affinity', 'semantic_sim', 'bm25_score', 'experience_affinity', 
        'skill_depth_affinity', 'availability_affinity', 'responsiveness_affinity', 
        'credential_affinity', 'trajectory_affinity', 'quality_score', 'penalties', 'final_score'
    ]
    f.write(",".join(cols) + "\n")
    for _, row in ranked1.iterrows():
        line = ",".join(str(row[c]) for c in cols)
        f.write(line + "\n")
    f.write("```\n\n")
    
    f.write("# 7. V2 Reproducibility Check\n\n")
    r1_ids = ranked1['candidate_id'].tolist()
    r2_ids = ranked2['candidate_id'].tolist()
    
    is_identical = (r1_ids == r2_ids)
    f.write(f"Identical Top 20 Candidates: {is_identical}\n")
    f.write(f"Run 1 Top 5: {r1_ids[:5]}\n")
    f.write(f"Run 2 Top 5: {r2_ids[:5]}\n")
    
    r1_scores = ranked1['final_score'].tolist()
    r2_scores = ranked2['final_score'].tolist()
    is_scores_identical = (r1_scores == r2_scores)
    f.write(f"Identical Scores: {is_scores_identical}\n")
