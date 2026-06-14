import os
import glob
import json
import asyncio
import csv
import traceback
import google.generativeai as genai

# Setup paths
BASE_DIR = r"C:\Users\krish\Documents\signalhire\backend"
VALIDATION_DIR = os.path.join(BASE_DIR, "real_world_resume_validation")
RAW_DIR = os.path.join(VALIDATION_DIR, "raw_resumes")
os.makedirs(RAW_DIR, exist_ok=True)

# Important: set up imports so we can use backend modules
import sys
sys.path.append(BASE_DIR)
from app.services.parsing import parse_resume_bytes

# Initialize Gemini for layout classification
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

layout_model = genai.GenerativeModel("gemini-2.5-flash")

async def classify_layout(text: str) -> str:
    """Classifies layout type using Gemini."""
    if not text.strip():
        return "scanned" # likely failed OCR or pure image
        
    prompt = f"""
    Based on the structural patterns in this extracted resume text, guess its likely original visual layout type.
    Options: single column, double column, table based, graphic heavy, scanned.
    
    If it looks like linear plain text, output 'single column'.
    If there are distinct side-bar sections or text that seems interleaved horizontally, output 'double column'.
    If it looks like tabular data, output 'table based'.
    If it looks very sparse or weirdly formatted with lots of short chunks, output 'graphic heavy'.
    If it has lots of OCR artifacts or typos, output 'scanned'.
    
    Return ONLY ONE of the options.
    
    Text snippet (first 1000 chars):
    {text[:1000]}
    """
    try:
        response = layout_model.generate_content(prompt)
        res = response.text.strip().lower()
        for opt in ["single column", "double column", "table based", "graphic heavy", "scanned"]:
            if opt in res:
                return opt
        return "single column"
    except Exception as e:
        return "single column"

async def process_resume(pdf_path: str):
    filename = os.path.basename(pdf_path)
    resume_id = filename.replace(".pdf", "")
    
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
        
    # Copy to raw_resumes for artifact persistence
    with open(os.path.join(RAW_DIR, filename), "wb") as f:
        f.write(file_bytes)
        
    parse_success = False
    title_success = False
    skill_success = False
    experience_success = False
    education_success = False
    certification_success = False
    layout_type = "unknown"
    root_cause = ""
    failure_file = ""
    failure_func = ""
    failure_line = ""
    parsed = {}
    graph_metrics = {}
    
    try:
        # Actually run the production parser
        parsed = await parse_resume_bytes(file_bytes, filename)
        parse_success = True
        
        # Check extraction success
        if parsed.get("current_title") and str(parsed["current_title"]).strip() != "Unknown Role":
            title_success = True
        if parsed.get("skills") and len(parsed["skills"]) > 0:
            skill_success = True
        if parsed.get("career_history") and len(parsed["career_history"]) > 0:
            experience_success = True
        if parsed.get("education") and len(parsed["education"]) > 0:
            education_success = True
        if isinstance(parsed.get("certifications"), list):
            certification_success = True
            
        graph_metrics = {
            "total_years": parsed.get("total_years_of_experience", 0),
            "promotion_count": parsed.get("career_history", [{}])[0].get("promotion_count", 0) if parsed.get("career_history") else 0,
        }
        # Actually wait, AIPipeline doesn't put promotion_count in the root dict, but I can compute it or look it up.
        # Let me just grab what is available. I will actually add the graph metrics to the root of parsed in ai.py.
            
        raw_text = parsed.get("_meta", {}).get("raw_extracted_text", "")
        if not raw_text:
            # Maybe confidence was high, so raw text wasn't saved in _meta.
            # Just try to classify layout using the parsed summary/headline as fallback or default to single column
            raw_text = parsed.get("summary", "")
            
        layout_type = await classify_layout(raw_text)
            
    except Exception as e:
        parse_success = False
        root_cause = str(e)
        # Extract traceback
        tb = traceback.extract_tb(e.__traceback__)
        if tb:
            last_call = tb[-1]
            failure_file = os.path.basename(last_call.filename)
            failure_func = last_call.name
            failure_line = str(last_call.lineno)

    # Save output artifacts
    output_data = {
        "resume_id": resume_id,
        "parsed_output": parsed,
    }
    with open(os.path.join(VALIDATION_DIR, f"{resume_id}_output.json"), "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    return {
        "resume_id": resume_id,
        "layout_type": layout_type,
        "parse_success": parse_success,
        "title_success": title_success,
        "skill_success": skill_success,
        "experience_success": experience_success,
        "education_success": education_success,
        "certification_success": certification_success,
        "root_cause": root_cause,
        "failure_file": failure_file,
        "failure_func": failure_func,
        "failure_line": failure_line,
        "parsed_json": json.dumps(parsed)[:500] if not parse_success else "",
        "graph": parsed.get("career_graph", {})
    }

async def main():
    print("Collecting resumes...")
    pdf_files = glob.glob(os.path.join(BASE_DIR, "resume_*.pdf"))
    
    # Need exactly 50
    pdf_files = pdf_files[:50]
    print(f"Found {len(pdf_files)} resumes.")
    
    results = []
    for i, pdf_path in enumerate(pdf_files):
        print(f"Processing {i+1}/{len(pdf_files)}: {os.path.basename(pdf_path)}...")
        res = await process_resume(pdf_path)
        results.append(res)
        
    # Write Validation CSV v2
    validation_csv = os.path.join(VALIDATION_DIR, "experience_validation_v2.csv")
    with open(validation_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["resume_id", "layout_type", "parse_success", "title_success", "skill_success", "experience_success", "education_success", "certification_success"])
        for r in results:
            writer.writerow([r["resume_id"], r["layout_type"], r["parse_success"], r["title_success"], r["skill_success"], r["experience_success"], r["education_success"], r["certification_success"]])

    # Write Career Graph CSV
    graph_csv = os.path.join(VALIDATION_DIR, "career_graph_validation.csv")
    with open(graph_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["resume_id", "total_years", "relevant_years", "leadership_years", "promotion_count", "company_count", "career_velocity", "inversion_count"])
        for r in results:
            g = r.get("graph", {})
            writer.writerow([r["resume_id"], g.get("total_years", 0), g.get("relevant_years", 0), g.get("leadership_years", 0), g.get("promotion_count", 0), g.get("company_count", 0), g.get("career_velocity", 0), g.get("inversion_count", 0)])

    # Write Failure Report CSV
    failures = [r for r in results if not r["parse_success"] or not r["title_success"] or not r["skill_success"] or not r["experience_success"]]
    failure_csv = os.path.join(VALIDATION_DIR, "real_world_failure_report.csv")
    with open(failure_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["resume_id", "parser_output", "root_cause", "file", "function", "line"])
        for r in failures:
            # Identify specific missing feature if it didn't completely crash
            if r["parse_success"]:
                missing = []
                if not r["title_success"]: missing.append("title")
                if not r["skill_success"]: missing.append("skills")
                if not r["experience_success"]: missing.append("experience")
                r["root_cause"] = f"Missing fields: {', '.join(missing)}"
                
            writer.writerow([r["resume_id"], r["parsed_json"], r["root_cause"], r["failure_file"], r["failure_func"], r["failure_line"]])
            
    print(f"Done. Processed {len(results)}. Validation written to {validation_csv}. {len(failures)} failures written to {failure_csv}.")

if __name__ == "__main__":
    asyncio.run(main())
