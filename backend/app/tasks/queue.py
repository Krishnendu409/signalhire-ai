import asyncio
import traceback
from app.db.session import async_session
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.ranking import RankingJob
from app.services.parsing import parse_resume_bytes
from app.services.storage import download_resume
from app.services.embeddings import embed_document
from app.services.vector_store import index_candidate
from app.services.ranking import rank_candidates_for_job
from sqlalchemy import select


# Simple background task runner (no external queue needed)
class SimpleQueue:
    def __init__(self):
        self._tasks = {}

    def register(self, name, func):
        self._tasks[name] = func

    async def enqueue(self, name, **kwargs):
        func = self._tasks.get(name)
        if func:
            asyncio.create_task(self._run(func, **kwargs))

    async def _run(self, func, **kwargs):
        try:
            await func(**kwargs)
        except Exception:
            traceback.print_exc()


queue = SimpleQueue()


# ---------- Task Implementations ----------

async def process_resume(candidate_id: str):
    async with async_session() as db:
        result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
        candidate = result.scalar_one_or_none()
        if not candidate:
            return
        try:
            file_bytes = await download_resume(candidate.resume_file_key)
            filename = candidate.resume_file_key
            parsed = await parse_resume_bytes(file_bytes, filename)

            text_parts = [
                parsed.get("summary", ""),
                " ".join(s.get("name", "") for s in parsed.get("skills", [])),
                " ".join(e.get("title", "") for e in parsed.get("experiences", [])),
            ]
            embed_text = ". ".join(p for p in text_parts if p)
            embedding = await embed_document(embed_text)

            await index_candidate(
                candidate_id=str(candidate.id),
                embedding=embedding,
                payload={
                    "candidate_id": str(candidate.id),
                    "name": parsed.get("full_name", ""),
                    "title": parsed.get("current_title", ""),
                },
            )

            candidate.parsed_data = parsed
            candidate.embedding_ids = [str(candidate.id)]
            candidate.layout_complexity = parsed["_meta"]["layout_complexity"]
            candidate.extraction_confidence = parsed["_meta"]["extraction_confidence"]
            await db.commit()
        except Exception as e:
            candidate.parsed_data = {"error": str(e)}
            await db.commit()


async def process_ranking(ranking_job_id: str):
    async with async_session() as db:
        result = await db.execute(select(RankingJob).where(RankingJob.id == ranking_job_id))
        ranking_job = result.scalar_one_or_none()
        if not ranking_job:
            return
        try:
            job_result = await db.execute(select(Job).where(Job.id == ranking_job.job_id))
            job = job_result.scalar_one_or_none()
            if not job or not job.parsed_requirements:
                raise ValueError("Job not found or not parsed")

            candidates_result = await db.execute(
                select(Candidate).where(
                    Candidate.recruiter_id == job.recruiter_id,
                    Candidate.parsed_data.isnot(None),
                )
            )
            candidates = candidates_result.scalars().all()
            candidate_dicts = [
                {"id": str(c.id), "parsed_data": c.parsed_data} for c in candidates
            ]

            ranking_result = await rank_candidates_for_job(
                job_id=str(job.id),
                job_requirements=job.parsed_requirements,
                candidates=candidate_dicts,
            )

            ranking_job.status = "completed"
            ranking_job.total_candidates = ranking_result["total"]
            ranking_job.results = ranking_result
            await db.commit()
        except Exception as e:
            ranking_job.status = "failed"
            ranking_job.results = {"error": str(e)}
            await db.commit()


# Register tasks
queue.register("process_resume", process_resume)
queue.register("process_ranking", process_ranking)