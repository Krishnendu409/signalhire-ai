import json
import pandas as pd
import numpy as np
from hackathon_pipeline.engine import RankingEngine

print("Loading engine...")
engine = RankingEngine()

jds = {
    "Search": {
        "family": "Search Engineer",
        "title_terms": ["search", "engineer", "relevance", "ranking", "retrieval", "nlp", "machine learning"],
        "req_skills": ["python", "elasticsearch", "faiss", "machine learning", "nlp", "deep learning", "pytorch"],
        "keywords": ["search", "relevance", "ranking", "retrieval", "nlp", "machine learning", "ai", "data science"]
    },
    "Frontend": {
        "family": "Frontend Engineer",
        "title_terms": ["frontend", "engineer", "ui", "ux", "react", "javascript", "web"],
        "req_skills": ["javascript", "react", "css", "html", "typescript", "ui/ux", "next.js"],
        "keywords": ["frontend", "ui", "ux", "responsive", "web development", "react", "redux", "performance"]
    },
    "Sales": {
        "family": "Sales Manager",
        "title_terms": ["sales", "manager", "business", "development", "account", "executive", "revenue"],
        "req_skills": ["sales", "crm", "b2b", "negotiation", "leadership", "pipeline", "salesforce"],
        "keywords": ["sales", "revenue", "growth", "b2b", "crm", "quota", "pipeline", "territory", "saas"]
    }
}

results = []

for role, jd in jds.items():
    print(f"Running {role}...")
    feat_base = engine._extract_features(jd)
    ranked = engine._rank_features(feat_base)
    
    # take top 20
    top20 = ranked.head(20)
    for rank_idx, (_, row) in enumerate(top20.iterrows()):
        
        # Human readable explanation
        # Score decomposition:
        ta = float(row['title_affinity'] * engine.config['weights']['title_affinity'])
        sa = float(row['skill_affinity'] * engine.config['weights']['skill_affinity'])
        ca = float(row['career_affinity'] * engine.config['weights']['career_affinity'])
        ss = float(row['semantic_sim'] * engine.config['weights']['semantic_sim'])
        bm25 = float(row['bm25_score'] * engine.config['weights']['bm25_score'])
        qs = float(row['quality_score'] * engine.config['weights']['quality_score'])
        pen = float(row['penalties'])
        
        # Engine reason
        reason = []
        if row['title_affinity'] > 0.5: reason.append("Strong title match")
        if row['skill_affinity'] > 0.5: reason.append("Strong skill match")
        if row['career_affinity'] > 0.5: reason.append("Strong career keywords")
        if pen < 0: reason.append("Penalized for inconsistency")
        
        results.append({
            "Role": role,
            "Rank": rank_idx + 1,
            "Candidate ID": row['candidate_id'],
            "Title": row['current_title'],
            "Total Score": round(row['final_score'], 2),
            "TitleAff": round(ta, 2),
            "SkillAff": round(sa, 2),
            "CareerAff": round(ca, 2),
            "SemSim": round(ss, 2),
            "BM25": round(bm25, 2),
            "Quality": round(qs, 2),
            "Penalty": round(pen, 2),
            "Engine Reasoning": ", ".join(reason)
        })

df_res = pd.DataFrame(results)
# print(df_res.to_markdown(index=False))
df_res.to_csv('recruiter_alignment_results.csv', index=False)
print("Saved to recruiter_alignment_results.csv")
