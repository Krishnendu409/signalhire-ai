import json
import os
import pandas as pd

# Load all candidates into a dict for easy lookup
cands_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
if not os.path.exists(cands_path):
    cands_path = r"../" + cands_path

cands_db = {}
with open(cands_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                c = json.loads(line)
                cands_db[c['candidate_id']] = c
            except:
                pass

def print_cand(cid, rank_type, rank):
    c = cands_db.get(cid, {})
    p = c.get('profile', {}) or {}
    title = p.get('current_title', 'Unknown')
    yrs = p.get('years_of_experience', 0)
    
    career = c.get('career_history', []) or []
    roles = []
    for job in career[:3]:
        roles.append(f"{job.get('title', '')} at {job.get('company', '')}")
    
    skills = " ".join([s.get('name', '') for s in (c.get('skills', []) or [])])[:150] + "..."
    
    print(f"[{rank_type} #{rank}] {cid}")
    print(f"Title: {title}")
    print(f"Years Exp: {yrs}")
    print(f"Last 3 Roles: { ' -> '.join(roles) }")
    print(f"Skills Summary: {skills}")
    print("-" * 60)

# The New Top 20 IDs from the previous investigation
new_top_20 = [
    "CAND_0008425", "CAND_0005260", "CAND_0009024", "CAND_0002025", 
    "CAND_0009691", "CAND_0007596", "CAND_0004402", "CAND_0001930", 
    "CAND_0005303", "CAND_0006870", "CAND_0002344", "CAND_0001405", 
    "CAND_0007052", "CAND_0006538", "CAND_0004628", "CAND_0000273", 
    "CAND_0002285", "CAND_0000782", "CAND_0009515", "CAND_0006335"
]

# We need the Old Top 20.
old_top_20 = []
if os.path.exists("submission.csv"):
    df = pd.read_csv("submission.csv")
    old_top_20 = df['candidate_id'].head(20).tolist()
else:
    print("No submission.csv found for old top 20!")

print("=== OLD TOP 10 ===")
for i, cid in enumerate(old_top_20[:10]):
    print_cand(cid, "OLD", i+1)

print("\n=== NEW TOP 10 ===")
for i, cid in enumerate(new_top_20[:10]):
    print_cand(cid, "NEW", i+1)

