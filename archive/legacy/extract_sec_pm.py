import json
import pandas as pd
from hackathon_pipeline.engine import RankingEngine
import pprint

engine = RankingEngine()
engine.load_retrieval_indexes()

jds_phase2 = {
    'Security Engineer': {
        "family": "Security Engineer",
        "title_terms": ["security", "infosec", "appsec", "cybersecurity"],
        "req_skills": ["penetration testing", "owasp", "python", "cryptography", "firewall", "siem"],
        "keywords": ["vulnerability", "threat", "compliance", "audit"],
        "min_experience": 3, "max_experience": 12, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    'Product Manager': {
        "family": "Product Manager",
        "title_terms": ["product manager", "pm", "owner"],
        "req_skills": ["agile", "scrum", "jira", "roadmap", "analytics", "user research"],
        "keywords": ["strategy", "vision", "stakeholder", "execution"],
        "min_experience": 4, "max_experience": 15, "budget_lpa_max": 999.0, "work_mode": "flexible"
    }
}

for role, jd in jds_phase2.items():
    print(f"\n================ {role.upper()} ================")
    cands = engine.run_pipeline(jd, top_k=20, use_retrieval=True)
    for i, c in enumerate(cands):
        cid = c['candidate_id']
        f_vec = engine._extract_features(jd, target_cids=[cid]).iloc[0].to_dict()
        print(f"\nRank {i+1}: {c['title']} | Score: {c['final_score']:.2f}")
        print(f"Features: {json.dumps({k: round(v, 2) if isinstance(v, float) else v for k, v in f_vec.items() if 'affinity' in k or 'authenticity' in k or 'sim' in k})}")
