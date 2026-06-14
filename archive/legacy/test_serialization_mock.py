import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from hackathon_pipeline.engine import RankingEngine

def test():
    flat_c = {
        "candidate_id": "CAND-123",
        "profile": {
            "current_title": "Software Engineer",
            "years_of_experience": 5,
            "full_name": "Test User"
        },
        "career_history": [],
        "skills": [],
        "education": [],
        "redrob_signals": {
            "expected_salary_range_inr_lpa": {"max": 20},
            "open_to_work_flag": True
        },
        "certifications": []
    }
    jd = {
        "title": "Software Engineer",
        "min_experience": 3,
        "req_skills": ["Python"]
    }
    
    engine = RankingEngine(candidates_list=[flat_c])
    results = engine.run_pipeline(jd, top_k=10)
    
    print("--- 1. EXACT OUTPUT_RECORDS SNIPPET ---")
    print(json.dumps(results[0], indent=2))
    
    # Simulate exact ranking.py formatting (lines 97-122)
    formatted_results = []
    for r in results:
        # parsed_data is mocked
        parsed_data = {"open_to_work": True}
        
        # EXACT CODE FROM ranking.py:
        dimension_scores = {
            "experience_affinity": {"score": r.get("experience_affinity", 0)},
            "skill_depth": {"score": r.get("skill_depth", 0)},
            "domain_authenticity": {"score": r.get("domain_authenticity", 0)}
        }
        
        # Checking if frontend can read it!
        formatted_results.append({
            "id": r.get("candidate_id"),
            "dimension_scores": dimension_scores,
            # wait, ranking.py does NOT map availability_affinity!
        })
        
    print("\n--- 2. EXACT BACKEND JSON SNIPPET ---")
    print(json.dumps(formatted_results[0], indent=2))
    
    print("\n--- 3. EXACT FRONTEND MAPPED VALUE ---")
    fe_avail = formatted_results[0]['dimension_scores'].get('availability_affinity', {}).get('score', 0)
    print(f"Mapped frontend value: {fe_avail}")

    print("\n--- 4. RECRUITER FILTER VERIFICATION ---")
    req_avail = True
    # EXACT CODE FROM frontend/src/app/workspace/page.tsx line 40:
    # if (reqAvailability && (c.scores?.availability_affinity || 0) < 1.0) return false;
    scores = {} # from dimension_scores mapped to plain numbers
    for k, v in formatted_results[0]['dimension_scores'].items():
        scores[k] = v.get('score', 0)
    
    frontend_availability = scores.get('availability_affinity', 0)
    retained = not (req_avail and frontend_availability < 1.0)
    print(f"Retains Candidate: {retained}")

test()
