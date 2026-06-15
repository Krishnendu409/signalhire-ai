import json
import pandas as pd
import numpy as np
from hackathon_pipeline.engine import RankingEngine

print("Loading engine...")
engine = RankingEngine()

print("Running Sales Manager pipeline...")
sales_jd = {
    "family": "Sales Manager",
    "title_terms": ["sales", "manager", "business", "development", "account", "executive", "revenue", "director", "vp", "lead"],
    "req_skills": ["sales", "crm", "b2b", "negotiation", "leadership", "pipeline", "salesforce", "marketing", "quota"],
    "keywords": ["sales", "revenue", "growth", "b2b", "crm", "quota", "pipeline", "territory", "forecasting", "closing", "saas", "enterprise"]
}

# Get all rankings
feat_base = engine._extract_features(sales_jd)
ranked = engine._rank_features(feat_base)
ranked['rank'] = np.arange(1, len(ranked) + 1)

titles_to_test = [
    "Sales Manager",
    "Sales Director",
    "VP of Sales",
    "Account Executive",
    "Enterprise Account Executive",
    "Business Development Manager",
    "Revenue Operations Manager",
    "Customer Success Manager",
    "GTM Lead",
    "Territory Manager"
]

results = []

for title in titles_to_test:
    # Exact match or contains? Let's do a loose string match or exact match.
    # We will do exact match (case-insensitive) for occurrence count, and also a contains.
    mask_contains = ranked['current_title'].str.contains(r'\b' + title.lower() + r'\b', regex=True, case=False, na=False)
    mask_exact = ranked['current_title'].str.lower() == title.lower()
    
    subset = ranked[mask_contains]
    
    occurrences = len(subset)
    if occurrences > 0:
        highest_rank = subset['rank'].min()
        avg_rank = subset['rank'].mean()
        top_100 = len(subset[subset['rank'] <= 100])
        top_500 = len(subset[subset['rank'] <= 500])
        top_2000 = len(subset[subset['rank'] <= 2000])
    else:
        highest_rank = None
        avg_rank = None
        top_100 = 0
        top_500 = 0
        top_2000 = 0
        
    results.append({
        "Title": title,
        "Occurrences": occurrences,
        "Highest Rank": highest_rank,
        "Average Rank": avg_rank,
        "Top 100 Presence": top_100,
        "Top 500 Presence": top_500,
        "Top 2000 Presence": top_2000
    })

df_res = pd.DataFrame(results)
print(df_res.to_markdown(index=False))
df_res.to_csv('hidden_title_results.csv', index=False)
print("Saved to hidden_title_results.csv")
