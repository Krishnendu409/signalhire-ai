import os
import json
import random
import csv
import fitz
import asyncio
from parser_audit import GROUND_TRUTH
from app.services.parsing import parse_resume_bytes

# PHASE 1 — BENCHMARK FORENSICS
with open("benchmark_resume_inventory.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "source_location", "document_type", "size_kb", "page_count"])
    for i in range(1, 51):
        filename = f"resume_{i}.pdf"
        size = os.path.getsize(filename) / 1024
        
        doc = fitz.open(filename)
        pages = len(doc)
        doc.close()
            
        writer.writerow([filename, os.path.abspath(filename), "pdf", f"{size:.2f}", pages])

# We need the 50 parses
async def get_parses():
    parsed_cands = []
    for i in range(1, 51):
        filename = f"resume_{i}.pdf"
        with open(filename, "rb") as pdf_file:
            pd = await parse_resume_bytes(pdf_file.read(), filename)
            parsed_cands.append({"id": str(i), "parsed_data": pd})
    return parsed_cands

parsed_candidates = asyncio.run(get_parses())

# Sample 10 randomly
random.seed(42)
sampled_ids = random.sample(range(1, 51), 10)

# PHASE 2 — GROUND TRUTH VALIDATION
with open("ground_truth_validation.md", "w") as f:
    f.write("# Ground Truth Validation\n\n")
    for cid in sampled_ids:
        gt = next(c for c in GROUND_TRUTH if c["id"] == str(cid))
        parsed = next(c for c in parsed_candidates if c["id"] == str(cid))["parsed_data"]
        
        f.write(f"## Candidate {cid}\n")
        f.write("### A. Raw Extracted Text\n")
        f.write(f"```text\n{parsed.get('_meta', {}).get('raw_extracted_text', '')[:500]}...\n```\n\n")
        
        f.write("### B. Ground Truth Profile\n")
        f.write("```json\n")
        f.write(json.dumps({
            "title": gt["title"],
            "years_of_experience": gt["yoe"],
            "skills": gt["skills"],
            "education": gt["education"],
            "certifications": gt["certifications"]
        }, indent=2) + "\n```\n\n")
        
        f.write("### C. Parsed Profile\n")
        f.write("```json\n")
        f.write(json.dumps({
            "title": parsed["current_title"],
            "years_of_experience": parsed["total_years_of_experience"],
            "skills": [s["name"] for s in parsed["skills"]],
            "education": [e["degree"] for e in parsed["education"]],
            "certifications": parsed["certifications"]
        }, indent=2) + "\n```\n\n")
        
        f.write("### D. Exact Field Comparison\n")
        f.write(f"- Title Match: {gt['title'] == parsed['current_title']}\n")
        f.write(f"- YOE Match: {gt['yoe'] == parsed['total_years_of_experience']}\n")
        f.write(f"- Skills Match: {set(gt['skills']) == set(s['name'] for s in parsed['skills'])}\n")
        f.write(f"- Education Match: {bool(gt['education'] in [e['degree'] for e in parsed['education']])}\n")
        f.write(f"- Certifications Match: {set(gt['certifications']) == set(parsed['certifications'])}\n\n")

# PHASE 3 — SKILL PRECISION AUDIT
with open("skill_audit.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Resume ID", "Ground Truth Skills", "Extracted Skills", "True Positives", "False Positives", "False Negatives", "Precision", "Recall"])
    for cid in sampled_ids:
        gt = next(c for c in GROUND_TRUTH if c["id"] == str(cid))
        parsed = next(c for c in parsed_candidates if c["id"] == str(cid))["parsed_data"]
        
        gt_s = set(gt["skills"])
        ext_s = set(s["name"] for s in parsed["skills"])
        
        tp = gt_s & ext_s
        fp = ext_s - gt_s
        fn = gt_s - ext_s
        
        prec = len(tp) / len(ext_s) if ext_s else 0
        rec = len(tp) / len(gt_s) if gt_s else 0
        
        writer.writerow([cid, "; ".join(gt_s), "; ".join(ext_s), len(tp), len(fp), len(fn), f"{prec:.2f}", f"{rec:.2f}"])

# PHASE 4 — EXPERIENCE AUDIT
with open("experience_audit.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Resume ID", "Ground Truth YOE", "Parsed YOE", "Absolute Error"])
    for cid in sampled_ids:
        gt = next(c for c in GROUND_TRUTH if c["id"] == str(cid))
        parsed = next(c for c in parsed_candidates if c["id"] == str(cid))["parsed_data"]
        
        gt_yoe = gt["yoe"]
        parsed_yoe = parsed["total_years_of_experience"]
        writer.writerow([cid, gt_yoe, parsed_yoe, abs(gt_yoe - parsed_yoe)])

# PHASE 5 — EDUCATION AUDIT
with open("education_audit.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Resume ID", "Ground Truth Degree", "Parsed Degree", "Match Y/N"])
    for cid in sampled_ids:
        gt = next(c for c in GROUND_TRUTH if c["id"] == str(cid))
        parsed = next(c for c in parsed_candidates if c["id"] == str(cid))["parsed_data"]
        
        gt_edu = gt["education"]
        ext_edu = "; ".join([e["degree"] for e in parsed["education"]])
        match = "Y" if gt_edu in ext_edu else "N"
        writer.writerow([cid, gt_edu, ext_edu, match])

# PHASE 6 — CERTIFICATION AUDIT
with open("certification_audit.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Resume ID", "Ground Truth Certifications", "Parsed Certifications", "TP", "FP", "FN"])
    for cid in sampled_ids:
        gt = next(c for c in GROUND_TRUTH if c["id"] == str(cid))
        parsed = next(c for c in parsed_candidates if c["id"] == str(cid))["parsed_data"]
        
        gt_c = set(gt["certifications"])
        ext_c = set(parsed["certifications"])
        
        tp = gt_c & ext_c
        fp = ext_c - gt_c
        fn = gt_c - ext_c
        
        writer.writerow([cid, "; ".join(gt_c), "; ".join(ext_c), len(tp), len(fp), len(fn)])

# PHASE 7 — RANK IMPACT REPRODUCTION
from app.services.ranking import rank_candidates_for_job

jd_data = {
    "title": "Software Engineer",
    "family": "Frontend Engineer",
    "title_terms": ["frontend", "javascript", "react", "ui", "web"],
    "req_skills": ["javascript", "react", "html", "css", "typescript", "ui/ux", "next.js"],
    "min_experience": 2
}

async def run_ranks():
    gt_cands = []
    for c in GROUND_TRUTH:
        yoe = c["yoe"]
        sy = 2026 - yoe
        exps = [
            {
                "title": c["title"],
                "company": f"Company {c['id']}",
                "start_date": f"Jan {sy}",
                "end_date": "Present",
                "duration_months": yoe * 12,
                "bullets": ["Developed multiple applications."]
            }
        ]
        if sy < 2024:
            exps.append({
                "title": f"Junior {c['title']}",
                "company": "Old Company",
                "start_date": f"Feb {sy-2}",
                "end_date": f"Dec {sy-1}",
                "duration_months": 22,
                "bullets": ["Maintained legacy systems."]
            })
            
        mapped = {
            "current_title": c["title"],
            "total_years_of_experience": yoe,
            "skills": [{"name": s, "type": "hard"} for s in c["skills"]],
            "education": [{"degree": c["education"], "institution": "University"}],
            "certifications": c["certifications"],
            "experiences": exps,
        }
        gt_cands.append({"id": f"gt_{c['id']}", "parsed_data": mapped})
        
    r_gt = await rank_candidates_for_job("test", jd_data, gt_cands)
    r_pa = await rank_candidates_for_job("test", jd_data, parsed_candidates)
    return r_gt["results"], r_pa["results"]

ranked_gt, ranked_parsed = asyncio.run(run_ranks())

gt_rank_map = {r["candidate_id"].replace("gt_", ""): r["rank"] for r in ranked_gt}
parsed_rank_map = {str(r["candidate_id"]): r["rank"] for r in ranked_parsed}

rank_diffs = []

with open("rank_shift.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["resume_id", "ground_truth_rank", "parsed_rank", "absolute_rank_shift"])
    for cid in range(1, 51):
        try:
            gt_r = gt_rank_map[str(cid)]
            parsed_r = parsed_rank_map[str(cid)]
        except KeyError as e:
            print(f"KeyError: {e}")
            print("gt keys:", gt_rank_map.keys())
            print("parsed keys:", parsed_rank_map.keys())
            raise
        diff = abs(gt_r - parsed_r)
        rank_diffs.append(diff)
        writer.writerow([cid, gt_r, parsed_r, diff])

mean_diff = sum(rank_diffs) / len(rank_diffs)
rank_diffs.sort()
median_diff = rank_diffs[len(rank_diffs)//2] if len(rank_diffs) % 2 != 0 else (rank_diffs[len(rank_diffs)//2 - 1] + rank_diffs[len(rank_diffs)//2]) / 2.0
p95_diff = rank_diffs[int(len(rank_diffs) * 0.95)]
max_diff = rank_diffs[-1]

print(f"Mean Rank Shift: {mean_diff:.2f}")
print(f"Median Rank Shift: {median_diff:.2f}")
print(f"P95 Rank Shift: {p95_diff}")
print(f"Max Rank Shift: {max_diff}")
