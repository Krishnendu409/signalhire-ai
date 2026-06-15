import os
import asyncio
import json
import csv
import time
import fitz
from app.services.ai import AIPipeline

# Setup django environment to avoid any dependency issues if any
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'signalhire.settings')

async def run_benchmark():
    resume_dir = "sample_resumes"
    if not os.path.exists(resume_dir):
        print(f"Directory {resume_dir} not found.")
        return

    files = [f for f in os.listdir(resume_dir) if f.endswith(".pdf")]
    
    name_results = []
    title_results = []
    skill_results = []

    for idx, f in enumerate(files):
        print(f"Processing {idx+1}/{len(files)}: {f}")
        filepath = os.path.join(resume_dir, f)
        
        try:
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue

        start_t = time.time()
        parsed = await AIPipeline.parse_resume(text)
        dur = time.time() - start_t
        
        name_results.append({
            "filename": f,
            "extracted_name": parsed.get("full_name"),
            "confidence": parsed.get("name_confidence", 0),
            "parse_time_sec": round(dur, 4)
        })
        
        title_results.append({
            "filename": f,
            "extracted_title": parsed.get("current_title"),
            "raw_title": parsed.get("raw_title"),
            "confidence": parsed.get("title_confidence", 0)
        })
        
        skills = parsed.get("skills", [])
        skill_names = [s.get("name") for s in skills]
        skill_results.append({
            "filename": f,
            "skill_count": len(skills),
            "skills": " | ".join(skill_names),
            "confidence": parsed.get("skill_confidence", 0)
        })

    with open("name_extraction_benchmark.csv", "w", newline="") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=["filename", "extracted_name", "confidence", "parse_time_sec"])
        writer.writeheader()
        writer.writerows(name_results)

    with open("title_extraction_benchmark.csv", "w", newline="") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=["filename", "extracted_title", "raw_title", "confidence"])
        writer.writeheader()
        writer.writerows(title_results)

    with open("skill_extraction_benchmark.csv", "w", newline="", encoding="utf-8") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=["filename", "skill_count", "confidence", "skills"])
        writer.writeheader()
        writer.writerows(skill_results)

    print("Benchmarks complete.")
    
if __name__ == "__main__":
    asyncio.run(run_benchmark())
