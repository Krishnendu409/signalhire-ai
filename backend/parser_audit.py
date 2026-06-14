import os
import json
import asyncio
from fpdf import FPDF
import uuid
from app.services.parsing import parse_resume_bytes
from app.services.ranking import rank_candidates_for_job
import random

print("Starting Resume Parser Accuracy Audit...")

# Generate 50 diverse ground truth resumes dynamically
GROUND_TRUTH = []
names = ["Alice", "Bob", "Charlie", "Diana", "Evan", "Fiona", "George", "Hannah", "Ian", "Jack", 
         "Kelly", "Liam", "Mia", "Noah", "Olivia", "Paul", "Quinn", "Rachel", "Sam", "Tina"]
titles = ["Software Engineer", "Backend Engineer", "Frontend Developer", "Data Scientist", "Machine Learning Engineer"]
skills_pool = ["Python", "Java", "JavaScript", "C++", "AWS", "Docker", "Kubernetes", "React", "Node.js", "SQL", "Machine Learning", "TensorFlow", "PyTorch"]
degrees = ["BS Computer Science", "MS Data Science", "BTech IT", "PhD Machine Learning", "BA Graphic Design"]
certs = ["AWS Certified", "CISSP", "Scrum Master", "Azure Fundamentals"]

for i in range(1, 51):
    name = f"{random.choice(names)} {random.choice(['Smith', 'Johnson', 'Davis', 'Ross', 'Wright'])} {i}"
    email = f"user{i}@example.com"
    title = random.choice(titles)
    sy = random.randint(2010, 2022)
    yoe = 2026 - sy
    
    cand_skills = random.sample(skills_pool, k=random.randint(4, 7))
    cand_degree = random.choice(degrees)
    cand_certs = random.sample(certs, k=random.randint(0, 2))
    
    text = f"{name}\n{email}\n\nSummary:\nExperienced {title} with {yoe} years of experience.\n\n"
    text += f"Experience:\n{title}\nCompany {i}\nJan {sy} - Present\nDeveloped multiple applications.\n\n"
    if sy < 2024:
        text += f"Junior {title}\nOld Company\nFeb {sy-2} - Dec {sy-1}\nMaintained legacy systems.\n\n"
        
    text += f"Skills:\nProficient in {', '.join(cand_skills)}.\n\n"
    text += f"Education:\n{cand_degree}\nUniversity {i}\n\n"
    if cand_certs:
        text += f"Certifications:\n{', '.join(cand_certs)}\n\n"
        
    GROUND_TRUTH.append({
        "id": str(i),
        "name": name,
        "email": email,
        "title": title,
        "yoe": yoe + (1 if sy < 2024 else 0),
        "skills": cand_skills,
        "education": cand_degree.split()[0], # BS, MS, etc.
        "certifications": cand_certs,
        "text": text,
        "sy": sy
    })

# Write to PDFs
for item in GROUND_TRUTH:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in item["text"].split("\n"):
        pdf.cell(200, 10, txt=line, ln=1)
    pdf.output(f"resume_{item['id']}.pdf")

async def run_audit():
    results = []
    parsed_candidates = []
    
    # Run parsing
    for item in GROUND_TRUTH:
        with open(f"resume_{item['id']}.pdf", "rb") as f:
            pdf_bytes = f.read()
        
        parsed = await parse_resume_bytes(pdf_bytes, "test.pdf")
        
        extracted_name = parsed.get("full_name", "")
        extracted_email = parsed.get("contact", {}).get("email", "")
        extracted_title = parsed.get("current_title", "")
        extracted_yoe = parsed.get("total_years_of_experience", 0)
        
        extracted_skills = [s.get("name") for s in parsed.get("skills", [])]
        extracted_education = parsed.get("education", [])
        extracted_certifications = parsed.get("certifications", [])
        
        # Calculate Precision / Recall for skills
        gt_skills = set(item["skills"])
        ex_skills = set([s for s in extracted_skills if s])
        
        tp = len(gt_skills.intersection(ex_skills))
        precision = tp / len(ex_skills) if ex_skills else 0
        recall = tp / len(gt_skills) if gt_skills else 0
        
        results.append({
            "name_match": int(item["name"].lower() in extracted_name.lower()),
            "email_match": int(extracted_email == item["email"]),
            "title_match": int(extracted_title.lower() in item["title"].lower() or item["title"].lower() in extracted_title.lower()),
            "yoe_match": int(abs(extracted_yoe - item["yoe"]) <= 1), # Allow 1 year discrepancy
            "education_match": int(len(extracted_education) > 0 and extracted_education != []),
            "cert_match": int(set(extracted_certifications) == set(item["certifications"])),
            "skill_precision": precision,
            "skill_recall": recall
        })
        
        # Prepare for ranking simulation
        cand_record = {
            "id": str(item["id"]),
            "parsed_data": {
                "candidate_id": str(item["id"]),
                "profile": {
                    "full_name": extracted_name,
                    "current_title": extracted_title,
                    "years_of_experience": extracted_yoe
                },
                "skills": [{"name": s} for s in ex_skills],
                "career_history": [
                    {
                        "title": exp.get("title", ""),
                        "company": exp.get("company", ""),
                        "description": " ".join(exp.get("bullets", [])) if isinstance(exp.get("bullets"), list) else str(exp.get("bullets", "")),
                        "duration_months": exp.get("duration_months", 12)
                    } 
                    for exp in parsed.get("experiences", [])
                ],
                "education": extracted_education,
                "certifications": extracted_certifications,
                "redrob_signals": {"open_to_work_flag": True}
            }
        }
        parsed_candidates.append(cand_record)
        
        gt_career_history = [
            {
                "title": item["title"],
                "company": "Company",
                "description": "Developed multiple applications.",
                "duration_months": (2026 - int(item["sy"])) * 12
            }
        ]
        if int(item["sy"]) < 2024:
            gt_career_history.append({
                "title": f"Junior {item['title']}",
                "company": "Company",
                "description": "Maintained legacy systems.",
                "duration_months": 12
            })
            
        gt_cand = {
            "id": f"gt_{item['id']}",
            "parsed_data": {
                "candidate_id": f"gt_{item['id']}",
                "profile": {
                    "full_name": item["name"],
                    "current_title": item["title"],
                    "years_of_experience": item["yoe"]
                },
                "skills": [{"name": s} for s in item["skills"]],
                "career_history": gt_career_history,
                "education": [{"degree": item["education"]}],
                "certifications": item["certifications"],
                "redrob_signals": {"open_to_work_flag": True}
            }
        }
        parsed_candidates.append(gt_cand)
        
    # Aggregate metrics
    print("\n--- 50-RESUME BENCHMARK TABLE ---")
    print("ID | GT Title | Extracted Title | Title Match | GT Skills Count | Extracted Skills Count | Precision | Recall")
    for idx, r in enumerate(results):
        gt = GROUND_TRUTH[idx]
        cand = parsed_candidates[idx * 2]
        ext_title = cand["parsed_data"]["profile"]["current_title"]
        gt_skills_count = len(gt["skills"])
        ex_skills_count = len(cand["parsed_data"]["skills"])
        match_str = "Yes" if r["title_match"] else "No"
        print(f"{gt['id']:>2} | {gt['title']:>15} | {ext_title:>15} | {match_str:>11} | {gt_skills_count:>15} | {ex_skills_count:>22} | {r['skill_precision']*100:>8.1f}% | {r['skill_recall']*100:>6.1f}%")

    print("\n--- EXTRACTION METRICS ---")
    N = len(GROUND_TRUTH)
    name_acc = sum(r["name_match"] for r in results) / N
    email_acc = sum(r["email_match"] for r in results) / N
    title_acc = sum(r["title_match"] for r in results) / N
    yoe_acc = sum(r["yoe_match"] for r in results) / N
    edu_acc = sum(r["education_match"] for r in results) / N
    cert_acc = sum(r["cert_match"] for r in results) / N
    skill_prec = sum(r["skill_precision"] for r in results) / N
    skill_rec = sum(r["skill_recall"] for r in results) / N
    
    print(f"Name Extraction Accuracy: {name_acc*100:.1f}%")
    print(f"Email Extraction Accuracy: {email_acc*100:.1f}%")
    print(f"Current Title Accuracy: {title_acc*100:.1f}%")
    print(f"Years of Experience Accuracy: {yoe_acc*100:.1f}%")
    print(f"Education Extraction Accuracy: {edu_acc*100:.1f}%")
    print(f"Certification Extraction Accuracy: {cert_acc*100:.1f}%")
    print(f"Skill Precision: {skill_prec*100:.1f}%")
    print(f"Skill Recall: {skill_rec*100:.1f}%")
    
    # 2. Ranking Workflow Test
    # Job requirements
    job_req = {
        "title": "Software Engineer",
        "seniority": "senior",
        "required_hard_skills": ["Python", "Machine Learning", "Docker"],
        "required_soft_skills": [],
        "must_have_experience": "",
        "nice_to_have": [],
        "hidden_competencies": [],
        "domain_knowledge": ""
    }
    
    ranked_results = await rank_candidates_for_job("test_job", job_req, parsed_candidates)
    
    # Separate and compare ranks
    parser_ranks = {}
    gt_ranks = {}
    
    for r in ranked_results["results"]:
        cid = r["candidate_id"]
        if str(cid).startswith("gt_"):
            gt_ranks[str(cid).replace("gt_", "")] = r["rank"]
        else:
            parser_ranks[str(cid)] = r["rank"]
            
    rank_diffs = []
    print("\n--- RANK-IMPACT AUDIT ---")
    print("ID | GT Rank | Parsed Rank | Abs Rank Shift")
    for cid in parser_ranks:
        diff = abs(parser_ranks[cid] - gt_ranks[cid])
        rank_diffs.append(diff)
        print(f"{cid:>2} | {gt_ranks[cid]:>7} | {parser_ranks[cid]:>11} | {diff:>14}")
        
    rank_diffs.sort()
    avg_diff = sum(rank_diffs) / len(rank_diffs)
    median_diff = rank_diffs[len(rank_diffs)//2] if len(rank_diffs) % 2 != 0 else (rank_diffs[len(rank_diffs)//2 - 1] + rank_diffs[len(rank_diffs)//2]) / 2.0
    p95_index = int(len(rank_diffs) * 0.95) - 1
    p95_diff = rank_diffs[p95_index] if p95_index >= 0 else rank_diffs[0]
    max_diff = rank_diffs[-1]
    
    print("\n--- RANKING COMPARISON METRICS ---")
    print(f"Mean Rank Shift: {avg_diff:.2f} positions")
    print(f"Median Rank Shift: {median_diff:.2f} positions")
    print(f"P95 Rank Shift: {p95_diff} positions")
    print(f"Max Rank Shift: {max_diff} positions")

asyncio.run(run_audit())
