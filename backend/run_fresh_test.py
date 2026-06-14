import json
import asyncio
import uuid
from app.db.session import async_session
from app.models.user import User
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.ranking import RankingJob
from app.tasks.functions import process_resume, process_ranking

async def run_e2e():
    print("=== FRESH MACHINE E2E TEST (ASYNC) ===")
    user_id = uuid.uuid4()
    
    async with async_session() as db:
        # Create user
        user = User(id=user_id, email=f"test_{uuid.uuid4()}@signalhire.ai", role="recruiter")
        db.add(user)
        await db.commit()
    
        # 1. Create Job
        from app.services.ai import AIPipeline
        parsed_jd = await AIPipeline.parse_jd("Role: Senior Frontend Engineer. Skills: React, TypeScript, Redux, 5+ years experience.")
        
        job = Job(id=uuid.uuid4(), recruiter_id=user_id, title="Senior Frontend Engineer", raw_text="JD", parsed_requirements=parsed_jd, status="active")
        db.add(job)
        await db.commit()
        job_id = job.id
        print(f"SUCCESS: Job ID {job_id}")
        
        # 2. Upload Candidate
        import os
        cand = Candidate(id=uuid.uuid4(), recruiter_id=user_id, resume_file_key=os.path.abspath("test_resume.pdf"))
        db.add(cand)
        await db.commit()
        cand_id = cand.id
        print(f"SUCCESS: Candidate ID {cand_id}")
    
    # 3. Parse Candidate
    print("\n3. Processing Candidate Parsing (Background Task)...")
    res = await process_resume(str(cand_id))
    print(f"PARSING RESULT: {res}")
    
    # 4. Trigger Ranking
    async with async_session() as db:
        ranking = RankingJob(id=uuid.uuid4(), job_id=job_id, version=1, status="pending", total_candidates=1)
        db.add(ranking)
        await db.commit()
        rank_id = ranking.id
    
    print(f"\n4. Processing Ranking (Background Task)... Ranking ID {rank_id}")
    res = await process_ranking(str(rank_id))
    print(f"RANKING STATUS: SUCCESS")
    print(f"TOP CANDIDATE DATA: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    asyncio.run(run_e2e())
