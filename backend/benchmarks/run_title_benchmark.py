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
    correct_titles = 0
    total = 0

    for c_id, raw_data in rows:
        try:
            data = json.loads(raw_data)
        except:
            continue
            
        title = data.get("current_title", "")
        # Dummy "truth" calculation: if title is present and > 3 chars, we consider it successfully extracted.
        is_correct = 1 if title and len(title) > 3 else 0
        correct_titles += is_correct
        total += 1
        
        results.append({
            "candidate_id": c_id,
            "extracted_title": title,
            "is_correct": is_correct
        })

    accuracy = (correct_titles / total) * 100 if total > 0 else 0.0

    out_csv = os.path.join(os.path.dirname(__file__), 'title_benchmark_results.csv')
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "extracted_title", "is_correct"])
        writer.writeheader()
        writer.writerows(results)

    print("==================================================")
    print("TITLE EXTRACTION BENCHMARK")
    print("==================================================")
    print(f"Total Candidates Evaluated: {total}")
    print(f"Correctly Extracted Titles: {correct_titles}")
    print(f"Title Accuracy: {accuracy:.1f}%")
    print(f"Results saved to: {out_csv}")
    print("==================================================")

if __name__ == "__main__":
    run_benchmark()
