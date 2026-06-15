import pandas as pd
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

# Find one of each
hidden = ['revenue operations manager', 'customer success manager', 'enterprise account executive', 'territory manager', 'gtm lead']

for title in hidden:
    candidates = ranked[ranked['current_title'].str.lower() == title]
    if len(candidates) > 0:
        c = candidates.iloc[0]
        print(f"\n--- {title.upper()} ---")
        print(f"Rank: {c.name} (Wait, index is {c.name})")
        print(f"Final Score: {c['final_score']:.2f}")
        print(f"T_Fam: {c['t_fam']} | S_Fam: {c['s_fam']} | C_Fam: {c['c_fam']}")
        print(f"Title Aff: {c['title_affinity']:.2f} | Skill Aff: {c['skill_affinity']:.2f} | Career Aff: {c['career_affinity']:.2f}")
        print(f"Penalties: {c['penalties']}")
        print(f"Quality: {c['quality_score']:.2f}")
    else:
        print(f"{title} not found in dataset at all???")
