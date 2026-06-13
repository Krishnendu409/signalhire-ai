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
res = engine.run_pipeline(jd, top_k=100)

count_before = len(res)
count_exp = sum(1 for r in res if r.get('experience_affinity', 0) >= 1.0)
count_auth = sum(1 for r in res if r.get('domain_authenticity', 0) >= 0.8)
count_avail = sum(1 for r in res if r.get('availability_affinity', 0) >= 1.0)

print(f"Before: {count_before}")
print(f"Exp (>=1.0): {count_exp}")
print(f"Auth (>=0.8): {count_auth}")
print(f"Avail (>=1.0): {count_avail}")
