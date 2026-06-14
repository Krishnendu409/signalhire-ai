import asyncio
import json
from app.db.session import engine, Base
from app.api.jobs import create_job
from app.api.rankings import create_ranking, get_latest_ranking
from app.models.user import User

async def main():
    test_user = User(id="test-user-id", email="test@example.com")
    
    print("Testing ranking engine...")
    from app.services.ranking import rank_candidates_for_job
    
    job_reqs = {
        "title": "Senior Search Engineer",
        "required_hard_skills": ["Python", "Elasticsearch", "Machine Learning"]
    }
    
    results = await rank_candidates_for_job("test-job", job_reqs, [])
    print(f"Total returned: {results['total']}")
    if results['total'] > 0:
        top = results['results'][0]
        print(f"Top candidate: {top['title']} (Score: {top['final_score']})")
        print(f"Sample SemSim_Contrib: {top.get('SemSim_Contrib')}")
        print("SUCCESS! Pipeline unified and functional.")

if __name__ == "__main__":
    asyncio.run(main())
