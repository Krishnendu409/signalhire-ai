import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import SessionLocal
from app.models.ranking import RankingJob
from app.models.job import Job

async def main():
    async with SessionLocal() as db:
        res = await db.execute(
            select(RankingJob, Job).join(Job, RankingJob.job_id == Job.id)
        )
        for r, j in res.all():
            print(f'{j.title}: {r.status} - Candidates: {r.total_candidates}')
            if r.status == 'completed' and r.results:
                top = r.results.get('results', [])
                if top:
                    print(f"  Top match: {top[0].get('full_name')} ({top[0].get('final_score')})")
                    for cand in top[:3]:
                        print(f"    - {cand.get('full_name')} | Score: {cand.get('final_score')}")
                        print(f"      Missing: {cand.get('explanation', {}).get('missing_skills', [])}")
                else:
                    print('  No results in results object')
            elif r.status == 'failed':
                print(f"  Failed: {r.results.get('error')}")

import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
