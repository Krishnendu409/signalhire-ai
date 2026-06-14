import os
import time
import requests
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

BASE_URL = "http://127.0.0.1:8005/api"
HEADERS = {"Authorization": "demo-token-placeholder"}
RESUMES_DIR = "stress_test_resumes"
os.makedirs(RESUMES_DIR, exist_ok=True)

def generate_pdf(filename, lines):
    c = canvas.Canvas(filename, pagesize=letter)
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()

ROLES = [
    {"title": "Software Engineer", "domain": "Tech", "skills": ["Python", "SQL", "React"]},
    {"title": "Embedded Engineer", "domain": "Hardware", "skills": ["C", "RTOS", "ARM"]},
    {"title": "RF Engineer", "domain": "Hardware", "skills": ["RF Design", "ADS", "Antenna Design"]},
    {"title": "VLSI Engineer", "domain": "Hardware", "skills": ["ASIC", "SystemVerilog", "CMOS", "Verilog"]},
    {"title": "Telecom Engineer", "domain": "Telecom", "skills": ["LTE", "5G", "BGP"]},
    {"title": "Solar Engineer", "domain": "Energy", "skills": ["PVsyst", "Solar Design", "Renewable Energy"]},
    {"title": "Manufacturing Engineer", "domain": "Manufacturing", "skills": ["Lean Six Sigma", "SPC", "CNC"]},
    {"title": "Finance Analyst", "domain": "Finance", "skills": ["Financial Modeling", "Excel", "SQL"]},
    {"title": "Sales Manager", "domain": "Sales", "skills": ["CRM", "Salesforce", "B2B"]},
    {"title": "Clinical Research Associate", "domain": "Medical", "skills": ["GCP", "EDC", "Clinical Trials"]}
]

print("--- Starting Recruiter Workflow Test ---")

# Step 1: Clean DB (simulate) - for real we just do clean tests by unique job IDs.
for role in ROLES:
    title = role["title"]
    print(f"\\nTesting Role: {title}")
    
    # 1. JD Upload
    jd_text = f"We are hiring a {title} with strong {role['domain']} expertise. Required skills: {', '.join(role['skills'])}. Must have 3+ years experience."
    res = requests.post(f"{BASE_URL}/jobs", data={"title": title}, files={"file": ("jd.txt", jd_text.encode(), "text/plain")}, headers=HEADERS)
    job_id = res.json()["id"]
    parsed_jd = res.json()
    print("Parsed JD:", json.dumps(parsed_jd, indent=2))
    
    # 2. Resume Upload
    cand_name = f"{title.replace(' ', '')}Expert"
    pdf_path = os.path.join(RESUMES_DIR, f"{cand_name}.pdf")
    generate_pdf(pdf_path, [cand_name, f"Senior {title}", "5 years of experience", f"Skills: {', '.join(role['skills'])}", f"Domain: {role['domain']}"])
    
    with open(pdf_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/candidates/upload", files={"file": f}, headers=HEADERS)
        cand_id = res.json()["candidate_id"]
    
    # Check Candidate Parse payload
    time.sleep(1) # wait a sec for parse
    cand_res = requests.get(f"{BASE_URL}/candidates/{cand_id}", headers=HEADERS)
    print("Parsed Candidate:", json.dumps(cand_res.json()["parsed_data"], indent=2)[:500] + "...")
    
    # 3. Rank
    res = requests.post(f"{BASE_URL}/rankings/{job_id}", headers=HEADERS)
    print("Ranking Trigger:", res.json())
    
    time.sleep(3) # Wait for ranking
    res = requests.get(f"{BASE_URL}/rankings/{job_id}/latest", headers=HEADERS)
    ranking_data = res.json()
    if ranking_data.get("status") == "completed":
        print("Top Match:", json.dumps(ranking_data["results"][0], indent=2))
    else:
        print("Ranking Status:", ranking_data.get("status"))
        
    print("--------------------------------------------------")

print("E2E Test Complete.")
