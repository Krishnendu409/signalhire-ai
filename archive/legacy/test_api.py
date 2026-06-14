import requests
import time
import json

BASE_URL = "http://localhost:8000"

def run_test(role_name, jd_text):
    print(f"\n{'='*50}\nSubmitting JD: {role_name}\n{'='*50}")
    
    # 1. Start Investigation
    try:
        res = requests.post(f"{BASE_URL}/api/investigations", json={"raw_text": jd_text})
        res.raise_for_status()
        data = res.json()
        inv_id = data["investigation_id"]
        print(f"API Request (POST /api/investigations): SUCCESS")
        print(f"Investigation ID: {inv_id}")
    except Exception as e:
        print(f"Failed to start investigation: {e}")
        return

    # 2. Poll Status
    print("Polling status...")
    while True:
        try:
            status_res = requests.get(f"{BASE_URL}/api/investigations/{inv_id}/status")
            status_data = status_res.json()
            status = status_data["status"]
            print(f"Status: {status}")
            if status == "COMPLETED":
                break
            elif status == "FAILED":
                print("Investigation FAILED on backend.")
                return
            time.sleep(1)
        except Exception as e:
            print(f"Polling failed: {e}")
            return

    # 3. Get Results
    try:
        results_res = requests.get(f"{BASE_URL}/api/investigations/{inv_id}/results")
        results_data = results_res.json()
        candidates = results_data["results"]
        
        print("\nAPI Response (GET /api/investigations/{id}/results): SUCCESS")
        print(f"Total Candidates Returned: {len(candidates)}")
        print("\nTop 3 Candidates JSON Payload:")
        print(json.dumps(candidates[:3], indent=2))
        
    except Exception as e:
        print(f"Failed to get results: {e}")

jds = [
    ("Search Engineer", "Looking for a Senior Search Engineer with extensive experience in Python, Elasticsearch, FAISS, Pinecone, and Learning-to-Rank (LTR). Must have built vector retrieval pipelines."),
    ("Frontend Engineer", "We need a Senior Frontend Developer skilled in React, Next.js, TypeScript, and TailwindCSS. UI/UX architecture and state management experience is required."),
    ("Sales Manager", "Hiring an Enterprise Sales Manager. Need proven experience with quota attainment, Salesforce CRM, B2B pipeline generation, and Go-to-Market (GTM) strategies.")
]

for name, text in jds:
    run_test(name, text)
    time.sleep(2)
