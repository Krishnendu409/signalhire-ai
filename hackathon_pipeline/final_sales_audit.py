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

results = engine.run_pipeline(base_jd, top_k=2000)

print("\n=== 1. HIDDEN TITLE TEST ===")
hidden_titles = ['revenue operations manager', 'customer success manager', 'enterprise account executive', 'territory manager', 'gtm lead']
for title in hidden_titles:
    ranks = [r['rank'] for r in results if r['title'] == title]
    if ranks:
        print(f"  {title}: Highest rank {ranks[0]}")
    else:
        print(f"  {title}: Not found in top 2000")

print("\n=== 2. SYNONYM ROBUSTNESS ===")
synonyms = ['Sales Manager', 'Revenue Leader', 'GTM Leader', 'Head of Sales']
base_top100_ids = set([r['candidate_id'] for r in results[:100]])
for syn in synonyms:
    jd = base_jd.copy()
    jd['title_terms'] = [syn, "Account Executive", "Business Development Manager", "Sales Director", "VP of Sales", "Revenue Manager"]
    res = engine.run_pipeline(jd, top_k=100)
    syn_top100_ids = set([r['candidate_id'] for r in res])
    overlap = len(base_top100_ids.intersection(syn_top100_ids))
    print(f"  Overlap with '{syn}': {overlap}%")

print("\n=== 3. ADVERSARIAL CONTAMINATION ===")
adversarial = ['accountant', 'hr manager', 'marketing manager', 'salesforce developer', 'technical account manager']
for title in adversarial:
    ranks = [r['rank'] for r in results if r['title'] == title]
    if ranks:
        print(f"  {title}: Highest rank {ranks[0]}")
    else:
        print(f"  {title}: Not found in top 2000")

print("\n=== 4. SCORE VARIANCE AUDIT ===")
feat = engine._extract_features(base_jd)
ranked = engine._rank_features(feat)
top100 = ranked.head(100)

var_metrics = {}
for col in ['title_affinity', 'skill_affinity', 'career_affinity', 'semantic_sim', 'bm25_score', 'quality_score', 'penalties']:
    weight = engine.config['weights'].get(col, 1.0) if col != 'penalties' else 1.0
    contribs = top100[col] * weight
    var_metrics[col] = np.var(contribs)

total_var = sum(var_metrics.values()) if sum(var_metrics.values()) > 0 else 1.0
for col, v in var_metrics.items():
    print(f"  {col}: {(v/total_var)*100:.2f}%")
