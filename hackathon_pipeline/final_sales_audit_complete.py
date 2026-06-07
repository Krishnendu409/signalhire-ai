import pandas as pd
import numpy as np
import math
import json
from collections import Counter
from engine import RankingEngine

engine = RankingEngine()

# INJECT HIDDEN TITLES
hidden_titles = ['revenue operations manager', 'customer success manager', 'enterprise account executive', 'territory manager', 'gtm lead']
mock_candidates = []
for i, title in enumerate(hidden_titles):
    mock_candidates.append({
        'candidate_id': f'MOCK_{i}',
        'current_title': title,
        'current_company': 'Mock Corp',
        'quality_score': 0.8,
        'skills': [{'name': 'sales'}, {'name': 'crm'}, {'name': 'b2b'}, {'name': 'pipeline'}, {'name': 'account management'}],
        'career_history': [{'title': title, 'company': 'Mock Corp', 'duration_months': 36, 'description': 'Managed B2B enterprise sales and CRM pipeline.'}]
    })

df_mock = pd.DataFrame(mock_candidates)

# We must replace engine's df with the combined one
engine.df = pd.concat([engine.df, df_mock], ignore_index=True)

base_jd = {
    'family': 'Sales Manager',
    'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
    'title_terms': engine.config['role_families']['Sales Manager'],
    'req_skills': engine.config['skill_families']['Sales Manager']
}

print("Running baseline feature extraction for Sales Manager...")
feat_base = engine._extract_features(base_jd)
ranked_base = engine._rank_features(feat_base.copy())
top100_base = ranked_base.head(100)
base_ids = set(top100_base['candidate_id'])
top20_base_ids = set(ranked_base.head(20)['candidate_id'])

# SECTION 1: SYNONYM ROBUSTNESS
print("\n=== SECTION 1 — Synonym Robustness ===")
synonyms = ['Sales Manager', 'Revenue Leader', 'GTM Leader', 'Head of Sales']
for syn in synonyms:
    jd_syn = base_jd.copy()
    jd_syn['family'] = syn
    feat_syn = engine._extract_features(jd_syn)
    ranked_syn = engine._rank_features(feat_syn.copy())
    syn_top100_ids = set(ranked_syn.head(100)['candidate_id'])
    syn_top20_ids = set(ranked_syn.head(20)['candidate_id'])
    
    overlap_100 = len(base_ids.intersection(syn_top100_ids))
    overlap_20 = len(top20_base_ids.intersection(syn_top20_ids))
    union_100 = len(base_ids.union(syn_top100_ids))
    jaccard = overlap_100 / union_100 if union_100 > 0 else 0.0
    
    print(f"{syn}:")
    print(f"  Top 100 overlap: {overlap_100}")
    print(f"  Top 20 overlap: {overlap_20}")
    print(f"  Jaccard similarity: {jaccard:.4f}")

# SECTION 2: HIDDEN TITLE STRESS TEST
print("\n=== SECTION 2 — Hidden Title Stress Test ===")
ranked_base['rank'] = range(1, len(ranked_base) + 1)
for t in hidden_titles:
    matches = ranked_base[ranked_base['current_title'] == t]
    if len(matches) > 0:
        best = matches.iloc[0]
        print(f"{t}:")
        print(f"  Rank: {best['rank']}")
        print(f"  Final score: {best['final_score']:.4f}")
        print(f"  Title Affinity: {best['title_affinity']:.4f}")
        print(f"  Skill Affinity: {best['skill_affinity']:.4f}")
        print(f"  Career Affinity: {best['career_affinity']:.4f}")
    else:
        print(f"{t}: Not found in dataset")


# SECTION 3: POST-FIX VARIANCE DECOMPOSITION
print("\n=== SECTION 3 — Post-Fix Variance Decomposition ===")
var_metrics = {}
for col in ['title_affinity', 'skill_affinity', 'career_affinity', 'semantic_sim', 'bm25_score', 'quality_score', 'penalties']:
    weight = engine.config['weights'].get(col, 1.0) if col != 'penalties' else 1.0
    contribs = top100_base[col] * weight
    var_metrics[col] = np.var(contribs)

total_var = sum(var_metrics.values()) if sum(var_metrics.values()) > 0 else 1.0
for col, v in var_metrics.items():
    print(f"{col} %: {(v/total_var)*100:.2f}%")


# SECTION 4: MONOCULTURE AUDIT
print("\n=== SECTION 4 — Monoculture Audit ===")
def calc_entropy(counts):
    total = sum(counts)
    return -sum((c/total)*math.log2(c/total) for c in counts if c > 0)

titles = top100_base['current_title'].dropna().tolist()
title_counts = list(Counter(titles).values())
entropy = calc_entropy(title_counts)
print(f"Title entropy for Sales Top 100: {entropy:.4f}")
print("Top titles in Top 100:")
for t, c in Counter(titles).most_common(5):
    print(f"  {t}: {c}")

trap_titles = engine.config['trap_titles']
trap_count = 0
for t in titles:
    if any(tr in t for tr in trap_titles) and 'engineer' not in t and 'sales' not in t and 'business' not in t and 'account' not in t:
        trap_count += 1
print(f"Accountants/HR/Random Executives in Top 100: {trap_count}")
