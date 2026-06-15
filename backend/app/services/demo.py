import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.services.ai import AIPipeline
from app.services.storage import upload_resume
from app.tasks.manager import task_queue

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PROJECT_ROOT.parent

# Bundled resume folders shipped with the hackathon repo
RESUME_DIRS = [
    REPO_ROOT / "sample_resumes",
    PROJECT_ROOT / "resumes",
    PROJECT_ROOT / "real_resumes",
    PROJECT_ROOT / "real_world_resume_validation" / "raw_resumes",
]
HACKATHON_JD_DOCX = (
    REPO_ROOT
    / "[PUB] India_runs_data_and_ai_challenge"
    / "India_runs_data_and_ai_challenge"
    / "job_description.docx"
)

DEFAULT_JD_TEXT = """Role: Senior Search Engineer
Skills: FAISS, Qdrant, Learning-to-Rank, Python, Elasticsearch
Experience: Production ML infrastructure, retrieval systems, vector databases
Responsibilities: Build and optimize candidate search and ranking pipelines at scale.
"""


async def _load_jd_text() -> str:
    if HACKATHON_JD_DOCX.exists():
        try:
            import docx  # type: ignore

            doc = docx.Document(str(HACKATHON_JD_DOCX))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            if text.strip():
                return text
        except Exception:
            pass
    return DEFAULT_JD_TEXT


async def _collect_resume_files() -> list[Path]:
    """Gather unique PDF resumes from all bundled folders."""
    seen: set[str] = set()
    files: list[Path] = []
    for directory in RESUME_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.pdf")):
            key = path.name.lower()
            if key in seen:
                continue
            seen.add(key)
            files.append(path)
    return files


async def create_hackathon_demo(user: User, db: AsyncSession) -> dict:
    """Create a demo investigation using all bundled resume PDF folders."""
    resume_files = await _collect_resume_files()
    if not resume_files:
        raise FileNotFoundError(
            "No PDF resumes found. Expected folders: sample_resumes/, backend/resumes/, "
            "backend/real_resumes/, backend/real_world_resume_validation/raw_resumes/"
        )

    raw_text = await _load_jd_text()
    parsed = await AIPipeline.parse_jd(raw_text)

    job = Job(
        id=uuid.uuid4(),
        recruiter_id=user.id,
        title="Senior Search Engineer (Hackathon Demo)",
        raw_text=raw_text,
        parsed_requirements=parsed,
        status="active",
    )
    db.add(job)
    await db.commit()
    job.embedding_id = str(job.id)
    await db.commit()

    task_ids: list[str] = []
    candidate_ids: list[str] = []

    for resume_path in resume_files:
        file_bytes = resume_path.read_bytes()
        candidate = Candidate(
            id=uuid.uuid4(),
            recruiter_id=user.id,
            job_id=job.id,
            resume_file_key="",
        )
        db.add(candidate)
        await db.commit()

        file_key = await upload_resume(file_bytes, str(candidate.id), resume_path.name)
        candidate.resume_file_key = file_key
        await db.commit()

        task_id = await task_queue.add_task("process_resume", candidate_id=str(candidate.id))
        task_ids.append(task_id)
        candidate_ids.append(str(candidate.id))

    return {
        "job_id": str(job.id),
        "title": job.title,
        "resume_count": len(resume_files),
        "task_ids": task_ids,
        "candidate_ids": candidate_ids,
        "message": f"Loaded {len(resume_files)} resumes from bundled resume folders",
        "sources": [str(d) for d in RESUME_DIRS if d.exists()],
    }
