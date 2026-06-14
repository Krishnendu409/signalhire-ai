import asyncio
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.ai import gemini_generate, RESUME_PARSE_PROMPT, RESUME_PARSE_SYSTEM
from hackathon_pipeline.engine import RankingEngine

resumes = [
    # 1
    """John Doe. Software Engineer. 5 years building Python backends at Google. Notice period: 30 days. Expected Salary: 20 LPA. Education: B.Tech in CS. Certifications: AWS Certified Developer. Open to work: Yes.""",
    # 2
    """Alice Smith. Data Scientist. 7 years of experience in ML and Data Engineering. Currently unemployed, looking for full-time roles immediately. Expected Salary: 150000 USD. Education: MS in CS, Stanford.""",
    # 3
    """Bob Jones. DevOps Engineer. Worked for 3 years at TechCorp. Not looking for a job right now. Education: B.S. in IT. Certifications: CKA, AWS SA.""",
    # 4
    """Charlie Brown. Product Manager. 10 years of total experience managing B2B SaaS. Notice period: 2 months. Expected pay: 30 LPA. Open to work. Education: MBA.""",
    # 5
    """Diana Prince. Frontend Dev. Experience: 2 years React/Vue. Available immediately. Salary expectation: 12 LPA. Education: B.Tech.""",
    # 6
    """Evan Wright. System Administrator. 15 years managing Linux servers. Looking for a change. Expected 25 LPA. Education: High School. Certifications: RHCE.""",
    # 7
    """Fiona Gallagher. Marketing Specialist. 4 years of SEO/SEM. Available with 2 weeks notice. Salary: 8 LPA. Education: B.A. in Comm. Certifications: Google Ads.""",
    # 8
    """George Costanza. Real Estate Agent. 1 year experience. Not open to work. Education: B.S. Architecture.""",
    # 9
    """Hannah Montana. Pop Star / Singer. 12 years performing. Looking for touring gigs. Expected: 100k per show. Education: Homeschooled. Certifications: None.""",
    # 10
    """Ian Malcolm. Mathematician. 20 years researching Chaos Theory. Open to consulting. Expected Salary: 50 LPA. Education: PhD Mathematics. Certifications: None."""
]

async def safe_parse(resume_text):
    prompt = RESUME_PARSE_PROMPT.replace("{resume_text}", resume_text)
    for attempt in range(10):
        try:
            return await gemini_generate(prompt=prompt, system=RESUME_PARSE_SYSTEM)
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                await asyncio.sleep(2 * (attempt + 1))
                continue
            raise e
    raise RuntimeError("Failed after 10 retries")

async def test():
    results = []
    
    # 1. Parsing Phase
    print("Parsing 10 resumes...")
    for i, r in enumerate(resumes):
        print(f"Parsing resume {i+1}...")
        parsed = await safe_parse(r)
        results.append(parsed)
        
    # Coverage Metrics
    yoe = otw = sal = edu = cert = 0
    for res in results:
        if res.get('total_years_of_experience') is not None and res.get('total_years_of_experience') > 0: yoe += 1
        if res.get('open_to_work') is True: otw += 1
        if res.get('expected_salary') is not None and res.get('expected_salary') > 0: sal += 1
        if res.get('education') and len(res['education']) > 0: edu += 1
        if res.get('certifications') and len(res['certifications']) > 0: cert += 1

    print("\n--- COVERAGE METRICS ---")
    print(f"years_of_experience extraction %: {(yoe/10)*100}%")
    print(f"open_to_work extraction %: {(otw/10)*100}%")
    print(f"expected_salary extraction %: {(sal/10)*100}%")
    print(f"education extraction %: {(edu/10)*100}%")
    print(f"certifications extraction %: {(cert/10)*100}%")
    
    # Per resume details and schema mapping
    engine_inputs = []
    for i, res in enumerate(results):
        print(f"\n--- RESUME {i+1} ---")
        cand_id = f"CAND-100{i}"
        print(f"candidate_id: {cand_id}")
        print(f"current_title: {res.get('current_title')}")
        print(f"years_of_experience: {res.get('total_years_of_experience')}")
        print(f"open_to_work: {res.get('open_to_work')}")
        print(f"certification count: {len(res.get('certifications', []))}")
        print(f"education count: {len(res.get('education', []))}")
        
        flat_c = {
            "candidate_id": cand_id,
            "profile": {
                "current_title": res.get("current_title", ""),
                "years_of_experience": res.get("total_years_of_experience", 0),
                "full_name": res.get("full_name", "Unknown")
            },
            "career_history": [
                {
                    "title": exp.get("title", ""),
                    "company": exp.get("company", ""),
                    "description": " ".join(exp.get("bullets", [])) if isinstance(exp.get("bullets"), list) else str(exp.get("bullets", ""))
                } 
                for exp in res.get("experiences", [])
            ],
            "skills": [{"name": s.get("name", "")} for s in res.get("skills", [])],
            "education": [{"degree": e.get("degree", ""), "institution": e.get("institution", "")} for e in res.get("education", [])],
            "redrob_signals": {
                "expected_salary_range_inr_lpa": {"max": res.get("expected_salary", 0)},
                "open_to_work_flag": res.get("open_to_work", False)
            },
            "certifications": [{"name": cert} for cert in res.get("certifications", [])]
        }
        engine_inputs.append(flat_c)
        if i == 0:
            print("\nPIPELINE TRACE FOR RESUME 1:")
            print("1. Parsed JSON snippet:", json.dumps({k: res[k] for k in ["total_years_of_experience", "open_to_work"]}, indent=2))
            print("2. Schema Mapped Engine Input: completed for resume 1 (details omitted to avoid logging sensitive candidate data)")
            
    # Rank through engine
    jd = {
        "title": "Software Engineer",
        "min_experience": 3,
        "req_skills": ["Python"]
    }
    
    engine = RankingEngine(candidates_list=engine_inputs)
    ranked = engine.run_pipeline(jd, top_k=10)
    
    print("\n--- RANKING VERIFICATION ---")
    pass_exp = False
    pass_avail = False
    for r in ranked:
        if r.get('experience_affinity', 0) > 0: pass_exp = True
        if r.get('availability_affinity', 0) > 0: pass_avail = True
        
    print(f"experience_affinity > 0 received by at least one candidate: {pass_exp}")
    print(f"availability_affinity > 0 received by at least one candidate: {pass_avail}")

asyncio.run(test())
