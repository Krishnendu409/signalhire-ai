import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hackathon_pipeline.engine import RankingEngine

jd = {
    "title": "Software Engineer",
    "min_experience": 3,
    "req_skills": ["Python", "SQL"]
}

engine = RankingEngine()
res = engine.run_pipeline(jd, top_k=5)

for i, r in enumerate(res):
    print(f"Candidate {i+1}: {r['candidate_id']}")
    print(f"  Backend experience_affinity: {r.get('experience_affinity', 0)}")
    print(f"  Backend skill_depth: {r.get('skill_depth_affinity', 0)}")
    print(f"  Backend domain_authenticity: {r.get('domain_authenticity', 0)}")
