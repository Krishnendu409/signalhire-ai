import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from hackathon_pipeline.engine import RankingEngine

def test():
    mapped = {
        "candidate_id": "TEST-1",
        "profile": {
            "current_title": "Developer",
            "years_of_experience": 5,
            "full_name": "Test User"
        },
        "career_history": [],
        "skills": [],
        "education": [],
        "redrob_signals": {
            "expected_salary_range_inr_lpa": {"max": 0},
            "open_to_work_flag": True
        },
        "certifications": []
    }
    jd = {
        "title": "Developer",
        "min_experience": 1,
        "req_skills": []
    }
    
    engine = RankingEngine(candidates_list=[mapped])
    output_records = engine.run_pipeline(jd)
    
    print("--- 1. EXACT OUTPUT_RECORDS SNIPPET ---")
    print(json.dumps(output_records[0], indent=2))
    
    # Simulate app.services.ranking mapping
    r = output_records[0]
    dimension_scores = {
        "experience_affinity": {"score": r.get("experience_affinity", 0)},
        "skill_depth": {"score": r.get("skill_depth", 0)},
        "domain_authenticity": {"score": r.get("domain_authenticity", 0)}
    }
    if "availability_affinity" in r: # Simulate if we patched ranking.py
        dimension_scores["availability_affinity"] = {"score": r.get("availability_affinity", 0)}
        
    # Wait, the prompt says "Do not modify... schema mapper".
    # I didn't modify ranking.py. Let's see what ranking.py ACTUALLY outputs without modifications.
    actual_dimension_scores = {
        "experience_affinity": {"score": r.get("experience_affinity", 0)},
        "skill_depth": {"score": r.get("skill_depth", 0)},
        "domain_authenticity": {"score": r.get("domain_authenticity", 0)}
    }
    
    print("\n--- 2. EXACT BACKEND JSON SNIPPET ---")
    print(json.dumps({
        "id": r.get("candidate_id"),
        "dimension_scores": actual_dimension_scores,
        "raw_engine_output": r # Backend receives this!
    }, indent=2))
    
    print("\n--- 3. EXACT FRONTEND MAPPED VALUE ---")
    fe_avail = actual_dimension_scores.get('availability_affinity', {}).get('score', 0)
    if "availability_affinity" not in actual_dimension_scores:
        print("availability_affinity: MISSING IN FRONTEND PAYLOAD")
    else:
        print(f"availability_affinity: {fe_avail}")

test()
