import json
import os
import sys

def run_regression(current_outputs, jd_name):
    print(f"Running Regression for {jd_name}...")
    baseline_path = os.path.join("archive_v1_frozen", f"top100_{jd_name.replace(' ', '_')}.json")
    
    if not os.path.exists(baseline_path):
        print(f"ERROR: Baseline not found at {baseline_path}")
        return False
        
    with open(baseline_path, 'r') as f:
        baseline = json.load(f)
        
    if len(current_outputs) != len(baseline):
        print(f"ERROR: Output length mismatch. Expected {len(baseline)}, got {len(current_outputs)}")
        return False
        
    for i in range(len(baseline)):
        base = baseline[i]
        curr = current_outputs[i]
        
        if base['candidate_id'] != curr['candidate_id']:
            print(f"ERROR: Rank {i+1} mismatch! Expected {base['candidate_id']}, got {curr['candidate_id']}")
            return False
            
        if abs(base['final_score'] - curr['final_score']) > 1e-5:
            print(f"ERROR: Score mismatch at Rank {i+1} for {base['candidate_id']}! Expected {base['final_score']}, got {curr['final_score']}")
            return False
            
    print(f"SUCCESS: {jd_name} perfectly matches V1 frozen baseline.")
    return True
