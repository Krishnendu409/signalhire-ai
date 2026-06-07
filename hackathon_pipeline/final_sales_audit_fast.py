import numpy as np
import pandas as pd
import re
import json
from engine import RankingEngine
import sys

engine = RankingEngine()

base_jd = {
    'family': 'Sales Manager',
    'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
    'title_terms': ["Sales Manager", "Account Executive", "Business Development Manager", "Sales Director", "VP of Sales", "Revenue Manager"],
    'req_skills': ["sales", "b2b", "crm", "salesforce", "hubspot", "quota", "pipeline", "outbound", "inbound", "lead generation", "negotiation", "closing", "prospecting", "account management"]
}

print("Extracting base features...")
feat = engine._extract_features(base_jd)
ranked = engine._rank_features(feat.copy())

def convert_to_results(ranked_df, top_k=2000):
    res = []
    for rank_idx, (_, row) in enumerate(ranked_df.head(top_k).iterrows()):
        res.append({
            'rank': rank_idx + 1,
            'candidate_id': row['candidate_id'],
            'title': str(row['current_title']).strip().lower()
        })
    return res

results = convert_to_results(ranked)

print("\n=== 1. HIDDEN TITLE TEST ===")
hidden_titles = ['revenue operations manager', 'customer success manager', 'enterprise account executive', 'territory manager', 'gtm lead']
for title in hidden_titles:
    ranks = [r['rank'] for r in results if title in r['title']]
    if ranks:
        print(f"  {title}: Highest rank {ranks[0]}")
    else:
        print(f"  {title}: Not found in top 2000")

print("\n=== 2. SYNONYM ROBUSTNESS ===")
synonyms = ['Sales Manager', 'Revenue Leader', 'GTM Leader', 'Head of Sales']
base_top100_ids = set([r['candidate_id'] for r in results[:100]])

t_text_series = feat['current_title'].fillna('').str.lower()

for syn in synonyms:
    title_terms = [syn, "Account Executive", "Business Development Manager", "Sales Director", "VP of Sales", "Revenue Manager"]
    t_hits_series = pd.Series(0, index=feat.index)
    for w in title_terms:
        t_hits_series += t_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
    
    feat_syn = feat.copy()
    feat_syn['title_affinity'] = (t_hits_series / 2.0).clip(upper=1.0)
    
    ranked_syn = engine._rank_features(feat_syn)
    res_syn = convert_to_results(ranked_syn, top_k=100)
    
    syn_top100_ids = set([r['candidate_id'] for r in res_syn])
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
top100 = ranked.head(100)

var_metrics = {}
for col in ['title_affinity', 'skill_affinity', 'career_affinity', 'semantic_sim', 'bm25_score', 'quality_score', 'penalties']:
    weight = engine.config['weights'].get(col, 1.0) if col != 'penalties' else 1.0
    contribs = top100[col] * weight
    var_metrics[col] = np.var(contribs)

total_var = sum(var_metrics.values()) if sum(var_metrics.values()) > 0 else 1.0
for col, v in var_metrics.items():
    print(f"  {col}: {(v/total_var)*100:.2f}%")
