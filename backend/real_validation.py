import os
import glob
import asyncio
import json
from app.services.ai import AIPipeline
from app.services.parsing import extract_text_from_pdf

async def run_real_validation():
    upload_dir = "real_resumes/"
    # Get 10 random pdfs
    pdfs = [f for f in glob.glob(os.path.join(upload_dir, "*.pdf"))]
    pdfs = pdfs[:10]
    
    out = "# Artifact 14 — REAL RESUME VALIDATION\n\n"
    
    for i, pdf in enumerate(pdfs):
        out += f"## Real Resume {i+1}: {os.path.basename(pdf)}\n"
        with open(pdf, "rb") as f:
            pdf_bytes = f.read()
        
        text, _ = await extract_text_from_pdf(pdf_bytes)
        parsed = await AIPipeline.parse_resume(text)
        
        out += "### Raw Extracted Text\n```text\n" + text[:500] + "...\n```\n\n"
        out += "### Parsed Output\n```json\n" + json.dumps(parsed, indent=2) + "\n```\n\n"
        out += f"**Skills:** {[s['name'] for s in parsed.get('skills', [])]}\n"
        out += f"**Experiences:** {len(parsed.get('experiences', []))} entries, {parsed.get('total_years_of_experience', 0)} YOE\n"
        out += f"**Education:** {[e['degree'] for e in parsed.get('education', [])]}\n"
        out += f"**Certifications:** {parsed.get('certifications', [])}\n\n"
        
    with open("artifact_14.md", "w") as f:
        f.write(out)

if __name__ == "__main__":
    asyncio.run(run_real_validation())
