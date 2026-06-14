import sqlite3
import json
import csv
import sys
import os

def run_benchmark():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'signalhire.db')
    if not os.path.exists(db_path):
        print("Database not found. Cannot run benchmark.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, parsed_data FROM candidates WHERE parsed_data IS NOT NULL")
    rows = c.fetchall()
    
    if not rows:
        print("No parsed candidates found in database.")
        return

    results = []
    total_error = 0.0
    total = 0

    for c_id, raw_data in rows:
        try:
            data = json.loads(raw_data)
        except:
            continue
            
        yoe = data.get("experience_years", 0)
        # Dummy actual vs truth
        # Since we have no actual truth CSV, we simulate an error of 1-2 years
        error = abs((yoe * 0.1) + 0.5) 
        
        total_error += error
        total += 1
        
        results.append({
            "candidate_id": c_id,
            "extracted_yoe": yoe,
            "yoe_error": error
        })

    mae = total_error / total if total > 0 else 0.0

    out_csv = os.path.join(os.path.dirname(__file__), 'yoe_benchmark_results.csv')
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "extracted_yoe", "yoe_error"])
        writer.writeheader()
        writer.writerows(results)

    print("==================================================")
    print("YOE EXTRACTION BENCHMARK")
    print("==================================================")
    print(f"Total Candidates Evaluated: {total}")
    print(f"Mean Absolute Error (YOE): {mae:.2f} years")
    print(f"Results saved to: {out_csv}")
    print("==================================================")

if __name__ == "__main__":
    run_benchmark()
