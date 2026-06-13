import asyncio
from app.services.ai import gemini_generate, RESUME_PARSE_SYSTEM, RESUME_PARSE_PROMPT

resumes = [
    """
    John Doe
    Software Engineer with 8 years of experience building scalable systems.
    Currently employed at TechCorp as a Senior Backend Dev.
    Expected salary: 150k USD.
    Notice period: 14 days.
    Open to work.
    """,
    """
    Jane Smith
    Data Scientist
    5 years analyzing data using Python and SQL.
    Currently at DataSys. Not actively looking but open to offers.
    """
]

async def test():
    for i, r in enumerate(resumes):
        prompt = RESUME_PARSE_PROMPT.replace("{resume_text}", r)
        result = await gemini_generate(prompt, RESUME_PARSE_SYSTEM)
        print(f"Resume {i+1}:")
        print(f"Years: {result.get('total_years_of_experience')}")
        print(f"Status: {result.get('current_employment_status')}")
        print(f"Open to Work: {result.get('open_to_work')}")
        print(f"Notice Period: {result.get('notice_period')}")
        print(f"Expected Salary: {result.get('expected_salary')}")
        print("---")

asyncio.run(test())
