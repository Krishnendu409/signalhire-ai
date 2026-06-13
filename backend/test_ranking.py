import asyncio, sys
sys.path.insert(0, '.')
from app.services.ranking import rank_candidates_for_job

async def test():
    job = {
        "title": "Software Engineer",
        "family": "Software Engineering",
        "title_terms": ["software", "engineer"],
        "req_skills": ["python", "aws", "docker"],
        "min_experience": 3,
        "education": "BS"
    }

    # Test: GT vs PA with near-identical data - only title differs
    cands = [
        {"id": "gt_0", "parsed_data": {
            "current_title": "Senior Software Engineer",
            "total_years_of_experience": 8,
            "skills": [{"name": "Python"}, {"name": "AWS"}, {"name": "Docker"}],
            "education": [{"degree": "BS", "institution": "University"}],
            "certifications": [],
            "experiences": [{"title": "SWE", "company": "Google", "duration_months": 96, "bullets": ["Built distributed systems"]}]
        }},
        {"id": "pa_0", "parsed_data": {
            "current_title": "Senior Software Engineer Google",
            "total_years_of_experience": 8,
            "skills": [{"name": "Python"}, {"name": "AWS"}, {"name": "Docker"}],
            "education": [{"degree": "BS", "institution": "University"}],
            "certifications": [],
            "experiences": [{"title": "SWE", "company": "Google", "duration_months": 96, "bullets": ["Built distributed systems"]}]
        }},
        {"id": "gt_1", "parsed_data": {
            "current_title": "Data Engineer",
            "total_years_of_experience": 5,
            "skills": [{"name": "Python"}, {"name": "Spark"}, {"name": "SQL"}],
            "education": [{"degree": "BTech", "institution": "University"}],
            "certifications": [],
            "experiences": [{"title": "Data Engineer", "company": "Snowflake", "duration_months": 60, "bullets": ["Built pipelines"]}]
        }},
        {"id": "pa_1", "parsed_data": {
            "current_title": "Data Engineer Snowflake",
            "total_years_of_experience": 5,
            "skills": [{"name": "Python"}, {"name": "Apache Spark"}, {"name": "SQL"}],
            "education": [{"degree": "BTech", "institution": "University"}],
            "certifications": [],
            "experiences": [{"title": "Data Engineer Snowflake", "company": "Snowflake", "duration_months": 60, "bullets": ["Built pipelines"]}]
        }},
    ]
    result = await rank_candidates_for_job("test", job, cands)
    print("Ranking results:")
    for r in result["results"]:
        score = r.get("final_score", "N/A")
        dims = r.get("dimension_scores", {})
        print(f"  id={r['id']}  rank={r['rank']}  score={score} dims={dims}")

    # Check if ranking function signature
    import inspect
    sig = inspect.signature(rank_candidates_for_job)
    print(f"\nrank_candidates_for_job signature: {sig}")

asyncio.run(test())
