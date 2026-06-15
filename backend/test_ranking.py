import asyncio
from app.db.session import async_session
from sqlalchemy import select
from app.models.job import Job
from app.services.ranking import rank_candidates_for_job
from app.models.candidate import Candidate
import json

async def main():
    async with async_session() as session:
        job_result = await session.execute(select(Job).limit(1))
        job = job_result.scalar_one_or_none()
        if not job:
            print("No job")
            return
            
        cand_result = await session.execute(
            select(Candidate).where(Candidate.recruiter_id == job.recruiter_id, Candidate.parsed_data.isnot(None))
        )
        candidates = [{"id": str(c.id), "parsed_data": c.parsed_data} for c in cand_result.scalars().all()]
        
        results = await rank_candidates_for_job(str(job.id), job.parsed_requirements, candidates)
        
        print("Top 10:")
        for r in results.get("results", [])[:10]:
            print(f"Cand: {r.get('candidate_id')}, Final Score: {r.get('final_score')}, SkillAff: {r.get('SkillAff_Contrib')}, TitleAff: {r.get('TitleAff_Contrib')}, Penalty: {r.get('Penalties')}, Transf: {r.get('transferability_evidence')}")

if __name__ == "__main__":
    asyncio.run(main())
