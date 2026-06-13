import requests
import json
import time
import io

BASE_URL = "http://localhost:8000"
HEADERS = {"Authorization": "Bearer demo-token-placeholder"}

print("--- END-TO-END UPLOAD EVIDENCE ---")
jd_text = "Looking for a Software Engineer with Python and React experience."
job_file = io.BytesIO(jd_text.encode("utf-8"))
job_file.name = "jd.txt"
resp = requests.post(f"{BASE_URL}/api/jobs", data={"title": "Software Engineer"}, files={"file": job_file}, headers=HEADERS)
job_id = resp.json()["id"]

for i in range(1, 6):
    file_path = f"resume_{i}.pdf"
    print(f"\n--- UPLOAD REQUEST {i} ---")
    with open(file_path, "rb") as f:
        u_resp = requests.post(f"{BASE_URL}/api/candidates/upload", files={"file": f}, headers=HEADERS)
        print(json.dumps(u_resp.json(), indent=2))
        
print("\nWaiting for parsing...")
time.sleep(5)

print("\n--- DATABASE & PARSED PAYLOAD (CANDIDATE 1) ---")
c1_id = u_resp.json()["candidate_id"]
c1_res = requests.get(f"{BASE_URL}/api/candidates/{c1_id}", headers=HEADERS)
print(json.dumps(c1_res.json(), indent=2)[:500] + "...")

print("\n--- RANKING PAYLOAD ---")
r_req = requests.post(f"{BASE_URL}/api/rankings/{job_id}", headers=HEADERS)
print(json.dumps(r_req.json(), indent=2))

for _ in range(5):
    time.sleep(2)
    latest_resp = requests.get(f"{BASE_URL}/api/rankings/{job_id}/latest", headers=HEADERS)
    ld = latest_resp.json()
    if ld.get("status") == "completed":
        print("\n--- FRONTEND PAYLOAD ---")
        print(json.dumps(ld, indent=2)[:800] + "...")
        break
