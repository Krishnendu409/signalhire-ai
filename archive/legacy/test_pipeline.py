import asyncio
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.services.ai import gemini_generate, RESUME_PARSE_PROMPT, RESUME_PARSE_SYSTEM

resume_text = """
John Doe
Software Engineer
Experience: 5 years building Python backends.
Currently employed but open to new opportunities.
Notice period: 30 days
Expected Salary: 20 LPA
Education: B.Tech in CS
Certifications: AWS Certified Developer
"""

async def test():
    print("--- 4. Resume Parser Verification ---")
    prompt = RESUME_PARSE_PROMPT.replace("{resume_text}", resume_text)
    
    try:
        response = await gemini_generate(prompt=prompt, system=RESUME_PARSE_SYSTEM)
        print(f"Gemini Response & Parsed JSON: {json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"EXCEPTION: {type(e).__name__}: {str(e)}")

asyncio.run(test())
