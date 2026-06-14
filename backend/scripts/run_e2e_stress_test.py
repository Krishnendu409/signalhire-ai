import os
import json
import time
import requests
import random
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit

BASE_URL = "http://127.0.0.1:8005/api"
HEADERS = {"Authorization": "demo-token-placeholder"}
RESUMES_DIR = "stress_test_resumes"
os.makedirs(RESUMES_DIR, exist_ok=True)

GOLD_DIR = r"C:\Users\krish\Documents\signalhire\backend\gold_dataset"

def generate_pdf(filename, text_lines):
    c = canvas.Canvas(filename, pagesize=letter)
    y = 750
    for line in text_lines:
        if not line:
            continue
        # simple wrap
        parts = simpleSplit(line, "Helvetica", 10, 500)
        for part in parts:
            if y < 50:
                c.showPage()
                y = 750
            c.drawString(50, y, part)
            y -= 15
        y -= 10
    c.save()

print("Loading gold dataset...")
with open(os.path.join(GOLD_DIR, "sample_candidates.json"), "r") as f:
    candidates = json.load(f)

# Randomly sample 100
random.seed(42)
sample_cands = random.sample(candidates, min(100, len(candidates)))

print(f"Generating {len(sample_cands)} PDF resumes...")
for i, c in enumerate(sample_cands):
    name = c.get("profile", {}).get("anonymized_name", f"Cand_{i}")
    lines = [
        name,
        c.get("profile", {}).get("headline", ""),
        c.get("profile", {}).get("summary", ""),
        "Experience:"
    ]
    for ch in c.get("career_history", []):
        lines.append(f"{ch.get('title', '')} at {ch.get('company', '')}")
        lines.append(f"{ch.get('start_date', '')} to {ch.get('end_date', '')}")
        lines.append(ch.get("description", ""))
    
    lines.append("Skills:")
    skills = [s.get("name", "") for s in c.get("skills", []) if isinstance(s, dict)]
    lines.append(", ".join(skills))
    
    pdf_path = os.path.join(RESUMES_DIR, f"{c['candidate_id']}.pdf")
    generate_pdf(pdf_path, lines)

print("Uploading to FastAPI...")
cand_ids = []
for c in sample_cands:
    pdf_path = os.path.join(RESUMES_DIR, f"{c['candidate_id']}.pdf")
    with open(pdf_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/candidates/upload", files={"file": (f"{c['candidate_id']}.pdf", f, "application/pdf")}, headers=HEADERS)
        if res.status_code == 200:
            cand_ids.append(res.json()["candidate_id"])

print(f"Uploaded {len(cand_ids)} candidates. Waiting for SAQ processing...")
time.sleep(15) # Wait for background processing

print("Loading JDs and triggering ranking...")
jd_files = [f for f in os.listdir(GOLD_DIR) if f.startswith("jd_") and f.endswith(".json")]

report_data = []

for jd_file in jd_files:
    with open(os.path.join(GOLD_DIR, jd_file), "r") as f:
        jd_data = json.load(f)
    
    title = jd_data.get("title", "Unknown Role")
    jd_text = f"Hiring a {title}. Domain: {jd_data.get('domain_knowledge', '')}. Requires: {', '.join(jd_data.get('required_hard_skills', []))}. Experience: {jd_data.get('must_have_experience', '')}"
    
    res = requests.post(f"{BASE_URL}/jobs", data={"title": title}, files={"file": ("jd.txt", jd_text.encode(), "text/plain")}, headers=HEADERS)
    job_id = res.json().get("id")
    
    # Rank
    requests.post(f"{BASE_URL}/rankings/{job_id}", headers=HEADERS)
    time.sleep(3)
    res = requests.get(f"{BASE_URL}/rankings/{job_id}/latest", headers=HEADERS)
    data = res.json()
    
    if "results" in data and len(data["results"]) > 0:
        top_cand = data["results"][0]
        report_data.append({
            "job_title": title,
            "top_candidate": top_cand.get("candidate", {}).get("name", "Unknown"),
            "top_score": top_cand.get("final_score", 0),
            "transferable_skills_found": len(top_cand.get("explanation", {}).get("adjacent_skills", [])),
            "status": "Success"
        })
    else:
        report_data.append({
            "job_title": title,
            "top_candidate": "None",
            "top_score": 0,
            "transferable_skills_found": 0,
            "status": "Failed"
        })

print("Writing performance_report.csv...")
with open("performance_report.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["job_title", "top_candidate", "top_score", "transferable_skills_found", "status"])
    writer.writeheader()
    writer.writerows(report_data)

print("E2E Stress Test complete!")
