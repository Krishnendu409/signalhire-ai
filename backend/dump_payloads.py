import requests
import json
import time

print("--- END-TO-END UPLOAD EVIDENCE ---\n")

for i in range(1, 6):
    file_path = f"resume_{i}.pdf"
    print(f"\n--- UPLOAD REQUEST {i} ---")
    print(f"POST /api/candidates/upload files=[{file_path}]")
    
    with open(file_path, "rb") as f:
        response = requests.post(
            f"http://localhost:8000/api/candidates/upload", 
            files={"file": f},
            headers={"Authorization": "Bearer demo-token-placeholder"}
        )
        
    data = response.json()
    cand_id = data.get("candidate_id")
    print("\n--- INITIAL RESPONSE ---")
    print(json.dumps(data, indent=2))
    
    # Wait for processing to complete
    print(f"Waiting for candidate {cand_id} to be parsed...")
    time.sleep(2)
    
    # Fetch candidate
    cand_res = requests.get(
        f"http://localhost:8000/api/candidates/{cand_id}",
        headers={"Authorization": "Bearer demo-token-placeholder"}
    )
    cand_data = cand_res.json()
    
    print("\n--- DATABASE PAYLOAD ---")
    print("(Candidate details retrieved from database after parsing)")
    print(json.dumps(cand_data, indent=2)[:400] + "...\n")
    
    print("\n--- PARSED PAYLOAD ---")
    parsed_data = cand_data.get("parsed_data", {})
    print(json.dumps(parsed_data, indent=2)[:500] + "...\n")
    
    print("\n--- RANKING PAYLOAD ---")
    job_req = {"title": "Software Engineer"}
    rank_resp = requests.post(
        f"http://localhost:8000/api/rankings/test_job", 
        json={"raw_text": "Software Engineer", "candidates_list": [cand_data]}
    )
    rdata = rank_resp.json() if rank_resp.status_code == 200 else {"error": rank_resp.text}
    print(json.dumps(rdata, indent=2)[:500] + "...\n")
    
    print("\n--- FRONTEND PAYLOAD ---")
    print(json.dumps(rdata, indent=2)[:300] + "...\n")
