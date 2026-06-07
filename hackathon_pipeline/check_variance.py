import pandas as pd
import numpy as np
from engine import RankingEngine
import json

engine = RankingEngine()
base_jd = {
    'family': 'Sales Manager',
    'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
    'title_terms': ["Sales Manager", "Account Executive", "Business Development Manager", "Sales Director", "VP of Sales", "Revenue Manager"],
    'req_skills': ["sales", "b2b", "crm", "salesforce", "hubspot", "quota", "pipeline", "outbound", "inbound", "lead generation", "negotiation", "closing", "prospecting", "account management"]
}

feat = engine._extract_features(base_jd)
ranked = engine._rank_features(feat.copy())

top100 = ranked.head(100)
print("\nTop 5 Final Scores:", top100['final_score'].head().tolist())
print("Top 5 Title Affinities:", top100['title_affinity'].head().tolist())
print("Top 5 Quality Scores:", top100['quality_score'].head().tolist())
print("Top 5 Penalties:", top100['penalties'].head().tolist())

var_metrics = {}
for col in ['title_affinity', 'skill_affinity', 'career_affinity', 'semantic_sim', 'bm25_score', 'quality_score', 'penalties']:
    weight = engine.config['weights'].get(col, 1.0) if col != 'penalties' else 1.0
    contribs = top100[col] * weight
    var_metrics[col] = np.var(contribs)

total_var = sum(var_metrics.values())
print("\nVariance Decomposition:")
for k, v in var_metrics.items():
    print(f"{k}: {(v / total_var * 100):.2f}%")
