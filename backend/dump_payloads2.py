import requests
import json
import time
import io

BASE_URL = "http://localhost:8000"
HEADERS = {"Authorization": "Bearer demo-token-placeholder"}

print("--- END-TO-END UPLOAD & RANKING EVIDENCE ---\n")

# 1. Create a Job
print("--- CREATING JOB ---")
jd_text = "Looking for a Software Engineer with Python and React experience."
job_file = io.BytesIO(jd_text.encode("utf-8"))
job_file.name = "jd.txt"

resp = requests.post(
    f"{BASE_URL}/api/jobs", 
    data={"title": "Software Engineer"},
    files={"file": job_file},
    headers=HEADERS
)
job_data = resp.json()
print(job_data)
job_id = job_data["id"]
print(f"Created Job ID: {job_id}\n")

# 2. Upload Resumes
cands = []
for i in range(1, 6):
    file_path = f"resume_{i}.pdf"
    print(f"--- UPLOAD REQUEST {i} ---")
    
    with open(file_path, "rb") as f:
        upload_resp = requests.post(
            f"{BASE_URL}/api/candidates/upload", 
            files={"file": f},
            headers=HEADERS
        )
        
    data = upload_resp.json()
    cand_id = data.get("candidate_id")
    cands.append(cand_id)
    print(json.dumps(data, indent=2))
    print()

# Wait for processing
print("Waiting for resumes to be parsed...")
time.sleep(10)

# Fetch candidate 1 payload
cand_res = requests.get(f"{BASE_URL}/api/candidates/{cands[0]}", headers=HEADERS)
cand_data = cand_res.json()
print("\n--- DATABASE PAYLOAD (CANDIDATE 1) ---")
print(json.dumps(cand_data, indent=2)[:400] + "...\n")

print("\n--- PARSED PAYLOAD (CANDIDATE 1) ---")
parsed_data = cand_data.get("parsed_data", {})
print(json.dumps(parsed_data, indent=2)[:500] + "...\n")

# 3. Trigger Ranking
print(f"--- RANKING REQUEST ---")
print(f"POST /api/rankings/{job_id}")
rank_req = requests.post(f"{BASE_URL}/api/rankings/{job_id}", headers=HEADERS)
print(json.dumps(rank_req.json(), indent=2))

# 4. Poll Ranking
print("\nPolling ranking...")
for _ in range(5):
    time.sleep(2)
    latest_resp = requests.get(f"{BASE_URL}/api/rankings/{job_id}/latest", headers=HEADERS)
    latest_data = latest_resp.json()
    status = latest_data.get("status")
    print(f"Ranking status: {status}")
    if status == "completed":
        print("\n--- RANKING PAYLOAD ---")
        print(json.dumps(latest_data, indent=2)[:600] + "...\n")
        break
    elif status == "failed":
        print("Ranking failed:", latest_data)
        break

print("\n--- FRONTEND PAYLOAD ---")
print(json.dumps(latest_data.get("results", [])[:1], indent=2)[:500] + "...\n")

