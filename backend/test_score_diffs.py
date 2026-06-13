import asyncio
import sys
import json
sys.path.insert(0, '.')
from app.services.ranking import rank_candidates_for_job
from validation_200 import RESUMES, JOB_REQ
from app.services.ai import AIPipeline

async def get_scores():
    gt_cands = []
    pa_cands = []
    
    # We will use the already parsed data if we can, but parsing takes 20s so we just re-parse.
    for i, r in enumerate(RESUMES):
        gt = r["gt"]
        yoe = gt["yoe"]
        sy = 2026 - yoe
        gt_mapped = {
            "current_title": gt["title"],
            "total_years_of_experience": yoe,
            "skills": [{"name": s, "type": "hard"} for s in gt["skills"]],
            "education": [{"degree": "BS", "institution": "University"}],
            "certifications": [],
            "experiences": [{"title": gt["title"], "company": "Company", "start_date": f"Jan {sy}", "end_date": "Present", "duration_months": yoe * 12, "bullets": ["Work"]}],
        }
        gt_cands.append({"id": f"gt_{i}", "parsed_data": gt_mapped})
        
        parsed = await AIPipeline.parse_resume(r["text"])
        pa_cands.append({"id": f"pa_{i}", "parsed_data": parsed})
        
    ranked_gt = await rank_candidates_for_job("test", JOB_REQ, gt_cands)
    ranked_pa = await rank_candidates_for_job("test", JOB_REQ, pa_cands)
    
    gt_scores = {r["id"].replace("gt_", ""): r.get("final_score", 0) for r in ranked_gt["results"]}
    pa_scores = {r["id"].replace("pa_", ""): r.get("final_score", 0) for r in ranked_pa["results"]}
    
    gt_ranks = {r["id"].replace("gt_", ""): r.get("rank", 200) for r in ranked_gt["results"]}
    pa_ranks = {r["id"].replace("pa_", ""): r.get("rank", 200) for r in ranked_pa["results"]}
    
    diffs = []
    for i in range(200):
        idx = str(i)
        gs = gt_scores.get(idx, 0)
        ps = pa_scores.get(idx, 0)
        gr = gt_ranks.get(idx, 200)
        pr = pa_ranks.get(idx, 200)
        
        if abs(gs - ps) > 0.1 or abs(gr - pr) > 5:
            diffs.append((i, gs, ps, gr, pr))
            
    print(f"Total candidates with score/rank differences > threshold: {len(diffs)}")
    print(f"ID | GT Score | PA Score | GT Rank | PA Rank")
    for d in diffs[:30]:
        print(f"{d[0]:03d} | {d[1]:8.2f} | {d[2]:8.2f} | {d[3]:7d} | {d[4]:7d}")

asyncio.run(get_scores())
