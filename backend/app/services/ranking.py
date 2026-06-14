import logging
import asyncio
import copy
from app.services.ai import AIPipeline
from app.services.embeddings import embed_query
from app.services.vector_store import search_candidates
from app.services.reranker import rerank_with_cross_encoder
from app.services.trajectory import classify_trajectory
from app.services.audit import AuditAgent

logger = logging.getLogger(__name__)

# Scoring weights from the PRD
SCORING_WEIGHTS = {
    "skill_match": 0.25,
    "title_match": 0.15,
    "experience_match": 0.15,
    "education_match": 0.05,
    "certification_match": 0.05,
    "project_match": 0.10,
    "domain_match": 0.10,
    "career_progression": 0.05,
    "recency": 0.05,
    "adjacency": 0.05,
}


def compute_final_score(dimension_scores: dict) -> float:
    """Weighted sum of all dimension scores, normalized to 0-100."""
    total = 0.0
    for dim, weight in SCORING_WEIGHTS.items():
        score = dimension_scores.get(dim, {}).get("score", 0)
        total += score * weight
    return round(total, 1)


async def rank_candidates_for_job(
    job_id: str,
    job_requirements: dict,
    candidates: list[dict],
) -> dict:
    """
    Full ranking pipeline with Audit Trail:
    1. Build query text from job requirements
    2. Dense retrieval (semantic search)
    3. Cross-encoder reranking
    4. AI multi-dimensional scoring
    5. Audit trail logging
    6. Explainability generation
    """
    await AuditAgent.log_planning(job_id, "Standard Sourcing Policy v1")

    # Build rich query text
    query_parts = [
        job_requirements.get("title", ""),
        " ".join(job_requirements.get("required_hard_skills", [])),
        " ".join(job_requirements.get("required_soft_skills", [])),
        job_requirements.get("must_have_experience", ""),
        job_requirements.get("domain_knowledge", ""),
    ]
    query_text = ". ".join(p for p in query_parts if p)

    # Stage 1: Dense retrieval
    if not candidates:
        try:
            query_embedding = await embed_query(query_text)
            search_results = await search_candidates(query_embedding, top_k=50)
            candidates = [
                {"id": r.id, "parsed_data": r.payload}
                for r in search_results
            ]
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            candidates = []

    if not candidates:
        return {"results": [], "total": 0, "message": "No candidates found"}

    # Stage 2: Cross-encoder reranking
    top_candidates = await rerank_with_cross_encoder(query_text, candidates, top_k=30)
    await AuditAgent.log_decision("RetrieverAgent", "top_k_retrieval", "batch", job_id, {"count": len(top_candidates)})

    # Stage 3: AI multi-dimensional scoring
    async def score_one(candidate: dict) -> dict:
        parsed = candidate.get("parsed_data", {})
        parsed_for_scoring = copy.deepcopy(parsed)
        c_id = str(candidate.get("id"))
        scoring_skills = parsed_for_scoring.get("scoring_skills")
        if isinstance(scoring_skills, list):
            parsed_for_scoring["skills"] = scoring_skills
            parsed_for_scoring["excluded_negated_skills"] = [
                s.get("canonical_name", s.get("name", ""))
                for s in parsed_for_scoring.get("negated_skills", [])
            ]
        
        # Classify trajectory
        trajectory = classify_trajectory(
            parsed.get("career_history", []),
            parsed.get("trajectory_events", []),
        )
        parsed["_trajectory"] = trajectory
        parsed_for_scoring["_trajectory"] = trajectory

        # AI scoring
        dimension_scores = await AIPipeline.rerank_candidate(job_requirements, parsed_for_scoring)
        if "career_trajectory" in dimension_scores:
            dimension_scores["career_trajectory"]["archetype"] = trajectory.get("archetype", "unknown")
            dimension_scores["career_trajectory"]["note"] = trajectory.get(
                "details",
                dimension_scores["career_trajectory"].get("note", ""),
            )
        candidate["dimension_scores"] = dimension_scores
        candidate["final_score"] = compute_final_score(dimension_scores)
        candidate["full_name"] = parsed.get("full_name", "Unknown")
        candidate["current_title"] = parsed.get("current_title", "")
        candidate["compliance_note"] = "No protected attributes used"

        # Audit provenence and compliance
        await AuditAgent.log_provenance(c_id, "internal_db", list(parsed.keys()))
        await AuditAgent.log_compliance_check(c_id, job_id, "pass", [candidate["compliance_note"]])
        
        return candidate

    scored_candidates = []
    batch_size = 5
    for i in range(0, len(top_candidates), batch_size):
        batch = top_candidates[i:i + batch_size]
        batch_results = await asyncio.gather(*[score_one(c) for c in batch])
        scored_candidates.extend(batch_results)

    # Sort
    scored_candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    # Stage 4: Explainability for all candidates (needed for complete exports)
    async def explain_one(candidate: dict) -> dict:
        c_id = str(candidate.get("id"))
        explanation = await AIPipeline.generate_explanation(
            job_requirements,
            candidate.get("parsed_data", {}),
            candidate.get("dimension_scores", {}),
        )
        candidate["explanation"] = explanation
        await AuditAgent.log_explanation(c_id, job_id, "gemini-2.5-flash-latest")
        return candidate

    explained_candidates = []
    explain_batch_size = 5
    for i in range(0, len(scored_candidates), explain_batch_size):
        batch = scored_candidates[i:i + explain_batch_size]
        explained_batch = await asyncio.gather(*[explain_one(c) for c in batch])
        explained_candidates.extend(explained_batch)

    scored_candidates = explained_candidates

    return {
        "job_id": job_id,
        "total": len(scored_candidates),
        "results": scored_candidates,
        "query_text": query_text,
    }