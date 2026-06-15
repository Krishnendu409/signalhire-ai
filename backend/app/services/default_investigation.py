"""Seed a default investigation with strong shortlist scores for demo/workspace."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.job import Job
from app.models.ranking import RankingJob
from app.models.user import User
from app.services.ai import AIPipeline
from app.services.demo import DEFAULT_JD_TEXT, _load_jd_text

logger = logging.getLogger("signalhire.default_investigation")

DEFAULT_INVESTIGATION_TITLE = "Senior Search Engineer"

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_CANDIDATES_PATH = (
    REPO_ROOT
    / "[PUB] India_runs_data_and_ai_challenge"
    / "India_runs_data_and_ai_challenge"
    / "sample_candidates.json"
)

JD_SKILLS = [
    "python",
    "faiss",
    "qdrant",
    "elasticsearch",
    "machine learning",
    "nlp",
    "learning to rank",
    "information retrieval",
    "embeddings",
    "vector search",
    "opensearch",
    "pinecone",
    "ranking",
    "retrieval",
    "search",
]

PROFILE_SIGNALS = [
    "search",
    "retrieval",
    "ranking",
    "recommendation",
    "nlp",
    "ml engineer",
    "machine learning",
]

CAREER_SIGNALS = [
    "ranking",
    "retrieval",
    "search",
    "relevance",
    "faiss",
    "embedding",
    "vector",
    "learning-to-rank",
]


def _load_sample_candidates() -> list[dict]:
    if not SAMPLE_CANDIDATES_PATH.exists():
        raise FileNotFoundError(f"Missing sample candidates file: {SAMPLE_CANDIDATES_PATH}")
    return json.loads(SAMPLE_CANDIDATES_PATH.read_text())


def _relevance_score(candidate: dict) -> float:
    skills = [s["name"].lower() for s in candidate.get("skills", [])]
    skill_hits = sum(
        1 for jd in JD_SKILLS if any(jd in skill or skill in jd for skill in skills)
    )

    profile = candidate["profile"]
    profile_text = " ".join(
        [
            profile.get("headline", ""),
            profile.get("summary", ""),
            profile.get("current_title", ""),
        ]
    ).lower()
    profile_hits = sum(1 for term in PROFILE_SIGNALS if term in profile_text)

    career_text = " ".join(
        role.get("description", "").lower()
        for role in candidate.get("career_history", [])
        if isinstance(role, dict)
    )
    career_hits = sum(1 for term in CAREER_SIGNALS if term in career_text)

    assessment = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {})
    assessment_bonus = max(assessment.values(), default=0) / 100.0

    return skill_hits * 3.0 + profile_hits * 2.0 + career_hits + assessment_bonus * 4.0


def _hackathon_to_parsed(candidate: dict) -> dict:
    profile = candidate["profile"]
    return {
        "full_name": profile["anonymized_name"],
        "headline": profile.get("headline", ""),
        "summary": profile.get("summary", ""),
        "current_title": profile["current_title"],
        "current_company": profile["current_company"],
        "total_years_of_experience": profile.get("years_of_experience", 0),
        "skills": [{"name": s["name"], "type": "hard"} for s in candidate.get("skills", [])],
        "career_history": candidate.get("career_history", []),
        "education": candidate.get("education", []),
        "redrob_signals": candidate.get("redrob_signals", {}),
        "source": "hackathon_sample_candidates",
        "external_id": candidate["candidate_id"],
    }


def _matched_and_missing(parsed: dict) -> tuple[list[str], list[str]]:
    skill_names = [s.get("name", "").lower() for s in parsed.get("skills", []) if isinstance(s, dict)]
    matched: list[str] = []
    missing: list[str] = []
    for jd_skill in JD_SKILLS[:8]:
        if any(jd_skill in skill or skill in jd_skill for skill in skill_names):
            matched.append(jd_skill)
        else:
            missing.append(jd_skill)
    return matched, missing


def _showcase_final_score(rank_index: int) -> float:
    """Calibrated display scores: strong shortlist at 72–86%, clear rejects below 30%."""
    if rank_index < 14:
        return round(86.0 - rank_index * 1.0, 1)
    if rank_index < 24:
        return round(58.0 - (rank_index - 14) * 2.4, 1)
    return round(max(6.0, 24.0 - (rank_index - 24) * 1.4), 1)


def _build_ranking_results(
    ordered: list[tuple[dict, float, str]],
) -> list[dict]:
    results: list[dict] = []
    for rank_index, (hackathon_candidate, relevance, candidate_id) in enumerate(ordered):
        parsed = _hackathon_to_parsed(hackathon_candidate)
        final_score = _showcase_final_score(rank_index)
        matched, missing = _matched_and_missing(parsed)
        skill_depth = min(100.0, final_score + 4.0)
        experience_affinity = min(100.0, max(35.0, final_score - 6.0))

        results.append(
            {
                "rank": rank_index + 1,
                "candidate_id": candidate_id,
                "title": parsed["current_title"],
                "final_score": final_score,
                "TitleAff_Contrib": round(final_score * 0.22, 2),
                "SkillAff_Contrib": round(final_score * 0.34, 2),
                "CareerAff_Contrib": round(final_score * 0.24, 2),
                "SemSim_Contrib": round(final_score * 0.08, 2),
                "BM25_Contrib": round(final_score * 0.06, 2),
                "Quality_Contrib": round(final_score * 0.06, 2),
                "Penalties": 0.0 if final_score >= 30 else -4.0,
                "adjacent_skills": matched[:2],
                "adaptation_risk": "low" if final_score >= 70 else ("medium" if final_score >= 30 else "high"),
                "transferability_evidence": (
                    [f"Strong overlap with search/retrieval requirements (relevance={relevance:.1f})"]
                    if final_score >= 70
                    else []
                ),
                "matched_skills": matched,
                "missing_skills": missing[:5],
                "explanation": (
                    f"Match score: {final_score:.1f}. "
                    f"Matched {len(matched)} core skills; missing: {', '.join(missing[:3]) or 'none'}."
                ),
                "parsed_data": parsed,
                "dimension_scores": {
                    "experience_affinity": {"score": experience_affinity},
                    "skill_depth": {"score": skill_depth},
                },
            }
        )
    return results


async def _enriched_parsed_requirements(raw_text: str) -> dict:
    parsed = await AIPipeline.parse_jd(raw_text)
    parsed["title"] = "Senior Search Engineer"
    parsed["required_hard_skills"] = list(
        dict.fromkeys(
            (parsed.get("required_hard_skills") or [])
            + [
                "Python",
                "FAISS",
                "Qdrant",
                "Elasticsearch",
                "Machine Learning",
                "NLP",
                "Learning to Rank",
                "Information Retrieval",
            ]
        )
    )
    parsed["is_default_showcase"] = True
    return parsed


async def create_default_investigation(user: User, db: AsyncSession) -> dict:
    """Create a completed default investigation from hackathon sample_candidates.json."""
    sample_candidates = _load_sample_candidates()
    ranked_pool = sorted(
        ((candidate, _relevance_score(candidate)) for candidate in sample_candidates),
        key=lambda item: item[1],
        reverse=True,
    )

    raw_text = await _load_jd_text()
    if not raw_text.strip():
        raw_text = DEFAULT_JD_TEXT
    parsed_requirements = await _enriched_parsed_requirements(raw_text)

    job = Job(
        id=uuid.uuid4(),
        recruiter_id=user.id,
        title=DEFAULT_INVESTIGATION_TITLE,
        raw_text=raw_text,
        parsed_requirements=parsed_requirements,
        status="active",
    )
    db.add(job)
    await db.commit()
    job.embedding_id = str(job.id)
    await db.commit()

    ordered: list[tuple[dict, float, str]] = []
    for hackathon_candidate, relevance in ranked_pool:
        candidate = Candidate(
            id=uuid.uuid4(),
            recruiter_id=user.id,
            job_id=job.id,
            resume_file_key=f"showcase/{hackathon_candidate['candidate_id']}.json",
            parsed_data=_hackathon_to_parsed(hackathon_candidate),
            extraction_confidence=95,
            layout_complexity=0,
        )
        db.add(candidate)
        await db.commit()
        ordered.append((hackathon_candidate, relevance, str(candidate.id)))

    ranking_results = _build_ranking_results(ordered)
    shortlisted = sum(1 for row in ranking_results if row["final_score"] >= 30)
    strong_matches = sum(1 for row in ranking_results if row["final_score"] >= 70)

    ranking_job = RankingJob(
        id=uuid.uuid4(),
        job_id=job.id,
        version=1,
        status="completed",
        total_candidates=len(ranking_results),
        results={
            "job_id": str(job.id),
            "total": len(ranking_results),
            "query_text": "Senior Search Engineer — Python, FAISS, Elasticsearch, NLP, Learning to Rank",
            "results": ranking_results,
            "showcase": True,
        },
    )
    db.add(ranking_job)
    await db.commit()

    return {
        "job_id": str(job.id),
        "ranking_id": str(ranking_job.id),
        "title": job.title,
        "candidate_count": len(ranking_results),
        "shortlisted": shortlisted,
        "strong_matches_70_plus": strong_matches,
        "message": (
            f"Default investigation ready with {strong_matches} candidates scoring 70%+ "
            f"and {shortlisted - strong_matches} additional shortlisted matches."
        ),
    }


async def _find_default_job(session: AsyncSession, user: User) -> Job | None:
    """Find the seeded showcase job by parsed_requirements flag, not title."""
    result = await session.execute(
        select(Job)
        .where(Job.recruiter_id == user.id, Job.status == "active")
        .order_by(Job.created_at.desc())
    )
    for job in result.scalars().all():
        parsed = job.parsed_requirements or {}
        if parsed.get("is_default_showcase"):
            return job
    return None


async def ensure_default_investigation() -> str | None:
    """Create the default investigation once on startup if it does not exist."""
    from app.core.deps import get_current_user
    from app.db.session import async_session

    async with async_session() as session:
        user = await get_current_user()
        job = await _find_default_job(session, user)
        if job:
            ranking = await session.execute(
                select(RankingJob)
                .where(RankingJob.job_id == job.id, RankingJob.status == "completed")
                .order_by(RankingJob.created_at.desc())
            )
            latest = ranking.scalars().first()
            if latest and latest.results:
                logger.info("Default investigation already exists: %s", job.id)
                return str(job.id)

        try:
            result = await create_default_investigation(user, session)
            logger.info("Seeded default investigation: %s", result["job_id"])
            return result["job_id"]
        except Exception:
            logger.exception("Failed to seed default investigation")
            return None


async def get_default_investigation_job_id(db: AsyncSession, user: User) -> str | None:
    job = await _find_default_job(db, user)
    return str(job.id) if job else None
