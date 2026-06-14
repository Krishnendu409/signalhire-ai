import pandas as pd
import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from hackathon_pipeline.engine import RankingEngine

def trace():
    print("1. Raw parser output")
    raw_output = {
        "full_name": "Test User",
        "current_title": "Developer",
        "total_years_of_experience": 5,
        "open_to_work": True
    }
    print(json.dumps(raw_output, indent=2))
    
    print("\n2. Schema mapped candidate object")
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
    print(json.dumps(mapped, indent=2))
    
    print("\n3. Exact candidate object received by RankingEngine")
    engine = RankingEngine(candidates_list=[mapped])
    print(json.dumps(engine.candidates_list[0], indent=2))
    
    print("\n4. Exact dataframe row after _load_dataset()")
    df_row = engine.df.iloc[0]
    print(f"open_to_work: {df_row['open_to_work']} (type: {type(df_row['open_to_work'])})")
    try:
        print(f"open_to_work_flag: {df_row['open_to_work_flag']}")
    except KeyError:
        print("open_to_work_flag: <KeyError - column does not exist>")
        
    print("\n5. Exact feature extraction output from _extract_features()")
    jd = {
        "title": "Developer",
        "min_experience": 1,
        "req_skills": []
    }
    feat = engine._extract_features(jd)
    feat_row = feat.iloc[0]
    print(f"availability_affinity: {feat_row['availability_affinity']} (type: {type(feat_row['availability_affinity'])})")
    
    print("\n6. Exact contribution to final score")
    ranked = engine._rank_features(feat)
    ranked_row = ranked.iloc[0]
    weight = engine.config['weights']['availability_affinity']
    contrib = ranked_row['availability_affinity'] * weight
    print(f"Contribution: {ranked_row['availability_affinity']} * {weight} = {contrib}")
    
    print("\n7. Final output records from run_pipeline")
    output = engine.run_pipeline(jd)
    print(json.dumps(output[0], indent=2))

trace()
