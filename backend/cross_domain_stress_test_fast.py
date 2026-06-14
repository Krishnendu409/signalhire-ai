import os
import time
import requests
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

BASE_URL = "http://127.0.0.1:8005/api"
HEADERS = {"Authorization": "demo-token-placeholder"}
RESUMES_DIR = "stress_test_resumes"

ROLES = [
    {"title": "Software Engineer", "domain": "Tech", "skills": ["Python", "SQL", "React"]},
    {"title": "Backend Engineer", "domain": "Tech", "skills": ["Node.js", "Postgres", "Redis"]},
    {"title": "Data Scientist", "domain": "Data", "skills": ["Machine Learning", "Python", "SQL"]},
    {"title": "Embedded Engineer", "domain": "Hardware", "skills": ["C", "RTOS", "ARM"]},
    {"title": "Electronics Engineer", "domain": "Hardware", "skills": ["PCB Design", "Altium", "Verilog"]},
    {"title": "RF Engineer", "domain": "Hardware", "skills": ["RF Design", "ADS", "Antenna"]},
    {"title": "VLSI Engineer", "domain": "Hardware", "skills": ["ASIC", "SystemVerilog", "CMOS"]},
    {"title": "Telecom Engineer", "domain": "Telecom", "skills": ["LTE", "5G", "BGP"]},
    {"title": "Manufacturing Engineer", "domain": "Engineering", "skills": ["Lean Six Sigma", "AutoCAD", "CNC"]},
    {"title": "Solar Engineer", "domain": "Energy", "skills": ["PVsyst", "AutoCAD", "Renewable Energy"]},
    {"title": "Automotive Engineer", "domain": "Automotive", "skills": ["CANalyzer", "MATLAB", "CATIA"]},
    {"title": "Finance Analyst", "domain": "Finance", "skills": ["Financial Modeling", "Excel", "SQL"]},
    {"title": "Investment Banking Analyst", "domain": "Finance", "skills": ["Valuation", "Excel", "PowerPoint"]},
    {"title": "Sales Manager", "domain": "Sales", "skills": ["CRM", "Salesforce", "B2B"]},
    {"title": "Marketing Manager", "domain": "Marketing", "skills": ["SEO", "Google Analytics", "Content Strategy"]},
    {"title": "Supply Chain Analyst", "domain": "Logistics", "skills": ["SAP", "Logistics", "Inventory Management"]},
    {"title": "HR Manager", "domain": "HR", "skills": ["Talent Acquisition", "Workday", "Employee Relations"]},
    {"title": "Clinical Research Associate", "domain": "Medical", "skills": ["GCP", "EDC", "Clinical Trials"]},
    {"title": "Product Manager", "domain": "Product", "skills": ["Agile", "Jira", "Roadmap"]},
    {"title": "Cybersecurity Engineer", "domain": "Security", "skills": ["Penetration Testing", "Firewalls", "Python"]}
]

def generate_pdf(filename, lines):
    c = canvas.Canvas(filename, pagesize=letter)
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()

os.makedirs(RESUMES_DIR, exist_ok=True)
results = {}

for role in ROLES:
    print(f"Setting up {role['title']}...")
    jd_text = f"Looking for a {role['title']} in {role['domain']}. Must have skills in {', '.join(role['skills'])}."
    res = requests.post(f"{BASE_URL}/jobs", data={"title": role["title"]}, files={"file": ("jd.txt", jd_text.encode(), "text/plain")}, headers=HEADERS)
    if res.status_code != 200:
        continue
    job_id = res.json()["id"]
    results[role["title"]] = {"job_id": job_id, "parsed_jd": res.json(), "candidates": []}

    candidates = [
        {"type": "Strong", "name": f"{role['title'].replace(' ', '')}StrongMatch", "skills": role["skills"], "yoe": 5},
        {"type": "Moderate", "name": f"{role['title'].replace(' ', '')}ModMatch", "skills": role["skills"][:1], "yoe": 3},
        {"type": "Poor", "name": f"{role['title'].replace(' ', '')}PoorMatch", "skills": ["Word", "Typing"], "yoe": 1}
    ]

    cand_ids = []
    for cand in candidates:
        pdf_path = os.path.join(RESUMES_DIR, f"{cand['name']}.pdf")
        generate_pdf(pdf_path, [cand["name"], f"{role['title']} at ACME Corp", f"{cand['yoe']} years of professional experience", f"Skills: {', '.join(cand['skills'])}", f"Domain: {role['domain']}"])
        with open(pdf_path, "rb") as f:
            res = requests.post(f"{BASE_URL}/candidates/upload", files={"file": f}, headers=HEADERS)
            if res.status_code == 200:
                cand_ids.append(res.json()["candidate_id"])

    res = requests.post(f"{BASE_URL}/rankings/{job_id}", json={"candidate_ids": cand_ids}, headers=HEADERS)

print("Waiting 15s for parsing and ranking to complete...")
time.sleep(15)

for role_title, data in results.items():
    job_id = data["job_id"]
    status = requests.get(f"{BASE_URL}/rankings/{job_id}/latest", headers=HEADERS).json()
    export_csv = requests.get(f"{BASE_URL}/rankings/{job_id}/export", headers=HEADERS).text
    data["csv"] = export_csv
    data["ranking_payload"] = status

with open("cross_domain_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Done.")
