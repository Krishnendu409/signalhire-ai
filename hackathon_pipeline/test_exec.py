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

execs = ranked[ranked['current_title'] == 'sales executive']
print("Sales Executive Ranks:")
print(execs[['candidate_id', 'final_score', 'title_affinity', 'quality_score', 'is_consistent', 'is_trap', 't_fam']].head(20))
