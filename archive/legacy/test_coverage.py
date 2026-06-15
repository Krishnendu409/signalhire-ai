import asyncio
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.services.ai import gemini_generate, RESUME_PARSE_PROMPT, RESUME_PARSE_SYSTEM

resumes = [
    """
    Alice Smith
    Data Scientist
    7 years of experience in ML and Data Engineering.
    Currently unemployed, looking for full-time roles immediately.
    Expected Salary: 150000 USD
    Education: MS in CS, Stanford
    """,
    """
    Bob Jones
    DevOps Engineer
    Worked for 3 years at TechCorp.
    Not looking for a job right now.
    Education: B.S. in IT
    Certifications: CKA, AWS SA
    """,
    """
    Charlie Brown
    Product Manager
    10 years of total experience.
    Notice period: 2 months. Expected pay: 30 LPA
    Open to work.
    Education: MBA
    """,
    """
    Diana Prince
    Frontend Dev
    Experience: 2 years.
    Available immediately. 
    Salary expectation: 12 LPA.
    Education: B.Tech
    """,
    """
    Evan Wright
    System Administrator
    15 years managing Linux servers.
    Looking for a change. Expected 25 LPA.
    Education: High School
    Certifications: RHCE
    """
]

async def test():
    print("--- 5. Coverage Audit ---")
    yoe = 0
    otw = 0
    sal = 0
    edu = 0
    cert = 0
    
    for i, r in enumerate(resumes):
        prompt = RESUME_PARSE_PROMPT.replace("{resume_text}", r)
        res = await gemini_generate(prompt=prompt, system=RESUME_PARSE_SYSTEM)
        
        if res.get('total_years_of_experience') is not None and res.get('total_years_of_experience') > 0:
            yoe += 1
        if res.get('open_to_work') is True:
            otw += 1
        if res.get('expected_salary') is not None and res.get('expected_salary') > 0:
            sal += 1
        if res.get('education') and len(res['education']) > 0:
            edu += 1
        if res.get('certifications') and len(res['certifications']) > 0:
            cert += 1

    print(f"years_of_experience extracted %: {(yoe/5)*100}%")
    print(f"open_to_work extracted %: {(otw/5)*100}%")
    print(f"expected_salary extracted %: {(sal/5)*100}%")
    print(f"education extracted %: {(edu/5)*100}%")
    print(f"certifications extracted %: {(cert/5)*100}%")

asyncio.run(test())
