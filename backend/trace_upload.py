import requests
import time
import json
import sqlite3

BASE_URL = "http://localhost:8000/api"

print("=== PRIORITY 3: DATA FLOW VERIFICATION ===")

# 1. Upload Resume
from fpdf import FPDF

# Generate PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="John Doe", ln=1)
pdf.cell(200, 10, txt="Senior Software Engineer", ln=1)
pdf.cell(200, 10, txt="5 years of experience", ln=1)
pdf.cell(200, 10, txt="Skills: Python, React, Next.js, FastAPI, PostgreSQL", ln=1)
pdf.output("test_resume.pdf")

print("\n--- 1. UPLOAD ---")
with open("test_resume.pdf", "rb") as f:
    files = {"file": ("test_resume.pdf", f, "application/pdf")}
    res = requests.post(f"{BASE_URL}/candidates/upload", files=files)
    
print("Status Code:", res.status_code)
upload_res = res.json()
print("Payload:", json.dumps(upload_res, indent=2))
candidate_id = upload_res.get("candidate_id")

if not candidate_id:
    print("Upload failed, stopping trace.")
    exit(1)

# Wait for background parsing to finish
print("\nWaiting for background parsing...")
time.sleep(3)

# 2. Database (Extraction & Parsing)
print("\n--- 2. DATABASE (EXTRACTION & PARSING) ---")
res = requests.get(f"{BASE_URL}/candidates/{candidate_id}")
if res.status_code == 200:
    cand_data = res.json()
    print("Parsed Schema Payload:")
    print(json.dumps(cand_data.get("parsed_data"), indent=2))
else:
    print("Candidate not found via API or parsing failed. Status:", res.status_code)
    print("Response:", res.text)

# 3. Create Job
print("\n--- 3. CREATING TEST JOB ---")
with open("test_resume.txt", "rb") as f:  # Use anything as JD
    files = {"file": ("jd.txt", f, "text/plain")}
    data = {"title": "Software Engineer"}
    res = requests.post(f"{BASE_URL}/jobs", files=files, data=data)
job_res = res.json()
print("Job created:", job_res)
job_id = job_res.get("id")

# 4. Ranking Engine Execution
print("\n--- 4. RANKING ENGINE ---")
res = requests.post(f"{BASE_URL}/rankings/{job_id}")
print("Trigger Ranking Status:", res.status_code)

time.sleep(3)
res = requests.get(f"{BASE_URL}/rankings/{job_id}/latest")
print("Poll Status:", res.json())

# 5. Frontend API / Results
print("\n--- 5. FRONTEND API ---")
res = requests.get(f"{BASE_URL}/investigations/{job_id}/results")
print("Investigation Status:", res.status_code)
if res.status_code == 200:
    results = res.json()
    for cand in results.get("candidates", []):
        if cand.get("candidate_id") == candidate_id:
            print("Found Traced Candidate in Output!")
            print(json.dumps(cand, indent=2))
            break
