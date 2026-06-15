import asyncio
import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))
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
    
    print("--- 1. EXACT OUTPUT_RECORDS (via backend return) ---")
    print(json.dumps(results[0], indent=2))
    
    # Simulate frontend mapping
    print("\n--- 2. EXACT FRONTEND MAPPED VALUE ---")
    fe_avail = results[0]['dimension_scores'].get('availability_affinity', {}).get('score', 0)
    print(f"availability_affinity score: {fe_avail}")
    
    print("\n--- 3. VERIFY RECRUITER FILTER ---")
    req_availability = True
    retained = True
    if req_availability and fe_avail < 1.0:
        retained = False
        
    print(f"Req Availability Retains Candidate: {retained}")
    
asyncio.run(test())
