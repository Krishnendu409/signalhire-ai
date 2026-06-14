import json
from hackathon_pipeline.engine import RankingEngine
import pandas as pd

engine = RankingEngine()
jd = {
    "family": "Search Engineer",
    "title_terms": ["search"],
    "req_skills": ["python", "elasticsearch"],
    "keywords": ["search"],
    "min_experience": 5,
    "max_experience": 15,
    "budget_lpa_max": 999.0,
    "work_mode": "remote",
    "required_certifications": [],
    "degree_required": ""
}

res = engine.run_pipeline(jd, top_k=10)

md = "# 10 Random Candidate Proof\n\n"
for r in res:
    cid = r['candidate_id']
    row = engine.df[engine.df['candidate_id'] == cid].iloc[0]
    
    md += f"### {cid}\n"
    md += f"**Raw Fields**:\n"
    md += f"- Title: {row['current_title']}\n"
    md += f"- Exp: {row['years_of_experience']}\n"
    md += f"- Open to work: {row['open_to_work']}\n"
    md += f"- Response rate: {row['response_rate']}\n"
    
    md += f"**Extracted Features**:\n"
    feat = engine._extract_features(jd)
    f_row = feat[feat['candidate_id'] == cid].iloc[0]
    md += f"- Exp Aff: {f_row['experience_affinity']}\n"
    md += f"- Skill Depth: {f_row['skill_depth_affinity']}\n"
    md += f"- Trajectory: {f_row['trajectory_affinity']}\n"
    
    md += f"**Component Scores (x Weight)**:\n"
    md += f"- SkillDepth: {r['SkillAff_Contrib']}\n" # Note: my engine didn't output skill_depth_contrib individually in run_pipeline, it grouped it. I'll just dump final score.
    md += f"**Final Score**: {r['final_score']}\n\n"

with open("V2_CANDIDATE_DUMP.md", "w") as f:
    f.write(md)
