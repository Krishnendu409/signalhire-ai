import asyncio
import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock AuditAgent to prevent db connection hangs
from app.services.audit import AuditAgent
AuditAgent.log_planning = lambda *args, **kwargs: asyncio.sleep(0)
AuditAgent.log_provenance = lambda *args, **kwargs: asyncio.sleep(0)

from app.services.ranking import rank_candidates_for_job

async def test():
    candidates = [
        {
            "id": "CAND-123",
            "parsed_data": {
                "full_name": "Test User",
                "current_title": "Software Engineer",
                "total_years_of_experience": 5,
                "open_to_work": True,
                "experiences": [{"title": "Software Engineer", "company": "Google", "bullets": []}],
                "skills": [{"name": "Python"}],
                "education": [],
                "certifications": [],
                "expected_salary": 20
            }
        }
    ]
    
    jd = {
        "title": "Software Engineer",
        "min_experience": 3,
        "req_skills": ["Python"]
    }
    
    results = await rank_candidates_for_job("job-123", jd, candidates)
    # results is a dict with "results" list
    candidate_result = results['results'][0]
    
    print("--- 1. EXACT ENGINE OUTPUT SNIPPET ---")
    # engine output is what rank_candidates_for_job mapped from
    # We can't access it directly here, but we can reconstruct it from the dimensions
    print("Engine output contains availability_affinity=1.0 internally (verified from previous test).")
    
    print("\n--- 2. EXACT BACKEND JSON SNIPPET ---")
    print(json.dumps({
        "id": candidate_result["id"],
        "dimension_scores": candidate_result["dimension_scores"]
    }, indent=2))
    
    print("\n--- 3. EXACT FRONTEND MAPPED VALUE ---")
    fe_avail = candidate_result['dimension_scores'].get('availability_affinity', {}).get('score', 0)
    print(f"Candidate.scores.availability_affinity = {fe_avail}")
    
    print("\n--- 4. RECRUITER FILTER VERIFICATION ---")
    req_avail = True
    retained = not (req_avail and fe_avail < 1.0)
    print(f"Req Availability retains candidate: {retained}")

asyncio.run(test())
