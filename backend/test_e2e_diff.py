import subprocess
import time
import requests
import json
from reportlab.pdfgen import canvas
import os
import signal

def generate_pdf(filename, text_lines):
    c = canvas.Canvas(filename)
    y = 800
    for line in text_lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()

# Generate dummy resumes
os.makedirs('resumes', exist_ok=True)
generate_pdf('resumes/alice.pdf', [
    "Alice Wright",
    "Senior Software Engineer at TechCorp",
    "5 years of experience",
    "Skills: Python, AWS, Kubernetes, React, Terraform",
    "Education: BS Computer Science",
    "Certifications: AWS Certified Solutions Architect",
    "Domain: E-commerce"
])

generate_pdf('resumes/bob.pdf', [
    "Bob Hardware",
    "Embedded Systems Engineer at Tesla",
    "4 years of experience",
    "Skills: C, C++, Verilog, ARM, RTOS",
    "Education: MS Electrical Engineering",
    "Domain: Automotive"
])

generate_pdf('resumes/charlie.pdf', [
    "Charlie Money",
    "Finance Analyst at Goldman Sachs",
    "3 years of experience",
    "Skills: Excel, Python, SQL, Financial Modeling",
    "Domain: Finance"
])

# Start server
print("Starting backend...")
with open("server.log", "w") as f:
    proc = subprocess.Popen(["python", "-m", "uvicorn", "app.main:app", "--port", "8005"], cwd=os.getcwd(), stdout=f, stderr=subprocess.STDOUT)

base_url = "http://127.0.0.1:8005/api"
headers = {"Authorization": "demo-token-placeholder"}

for i in range(15):
    try:
        if requests.get(f"{base_url}/health").status_code == 200:
            print("Backend is up!")
            break
    except:
        pass
    time.sleep(1)

jobs = [
    ("Software Engineer", "Senior Software Engineer\nMust have 5 years experience\nSkills: Python, AWS, Kubernetes\nDomain: E-commerce"),
    ("Embedded Engineer", "Embedded Engineer\nMust have 3 years experience\nSkills: C, RTOS\nDomain: Automotive"),
    ("Finance Analyst", "Finance Analyst\n2 years experience\nSkills: SQL, Excel\nDomain: Finance"),
]

job_ids = {}

print("--- Uploading JD ---")
for title, jd in jobs:
    res = requests.post(f"{base_url}/jobs", headers=headers, data={"title": title}, files={"file": ("jd.txt", jd.encode(), "text/plain")})
    data = res.json()
    job_ids[title] = data.get("id")
    print("Job Created:", title, "->", data.get("id"))

print("--- Uploading Resumes ---")
for fname in ['alice.pdf', 'bob.pdf', 'charlie.pdf']:
    with open(f"resumes/{fname}", "rb") as f:
        res = requests.post(f"{base_url}/candidates/upload", headers=headers, files={"file": (fname, f, "application/pdf")})
        print("Resume Uploaded:", fname, "->", res.json())

time.sleep(3)

results = {}
for title, j_id in job_ids.items():
    print(f"\n--- Ranking for {title} ---")
    requests.post(f"{base_url}/rankings/{j_id}", headers=headers)
    time.sleep(3)
    
    # Wait till complete
    for _ in range(5):
        status = requests.get(f"{base_url}/rankings/{j_id}/latest", headers=headers).json()
        if status.get("status") == "completed":
            print(f"Ranking completed for {title}")
            break
        time.sleep(2)
        
    # Get workspace to see parsed candidates or extract from ranking
    # The ranking payload usually has candidates and dimensions.
    # Let's just print the dimension scores for top candidates.
    print(json.dumps(status, indent=2))
    
    # Export reports
    rep = requests.get(f"{base_url}/rankings/{j_id}/export", headers=headers)
    print("CSV EXPORT:")
    print(rep.text[:1000])

proc.terminate()
