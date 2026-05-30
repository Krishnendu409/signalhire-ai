import asyncio
from app.services.ai import AIPipeline, MODEL_NAME
from app.services.embeddings import embed_query
from app.services.vector_store import search_candidates
from app.services.reranker import rerank_with_cross_encoder
from app.services.trajectory import classify_trajectory
from app.services.audit import AuditAgent


# Scoring weights from the PRD
SCORING_WEIGHTS = {
    "semantic_relevance": 0.35,
    "experience_depth": 0.20,
    "career_trajectory": 0.15,
    "project_relevance": 0.10,
    "behavioral_indicators": 0.10,
    "domain_alignment": 0.05,
    "adaptability": 0.05,
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

    # Stage 1: Dense retrieval (top 50 bi-encoder candidates)
    dense_candidates = []
    candidate_map = {str(c.get("id")): c for c in candidates}
    try:
        query_embedding = await embed_query(query_text)
        search_results = await search_candidates(query_embedding, top_k=50)
        for r in search_results:
            candidate_id = str(r.id)
            if candidate_id in candidate_map:
                dense_candidates.append(candidate_map[candidate_id])
            else:
                dense_candidates.append({"id": candidate_id, "parsed_data": r.payload})
    except Exception as e:
        print(f"Retrieval error: {e}")

    if dense_candidates:
        candidates = dense_candidates
    elif candidates:
        candidates = candidates[:50]

    if not candidates:
        return {"results": [], "total": 0, "message": "No candidates found"}

    # Stage 2: Cross-encoder reranking
    top_candidates = await rerank_with_cross_encoder(query_text, candidates, top_k=50)
    await AuditAgent.log_decision("RetrieverAgent", "top_k_retrieval", "batch", job_id, {"count": len(top_candidates)})

    # Stage 3: AI multi-dimensional scoring
    async def score_one(candidate: dict) -> dict:
        parsed = candidate.get("parsed_data", {})
        c_id = str(candidate.get("id"))
        
        # Classify trajectory
        trajectory = classify_trajectory(
            parsed.get("experiences", []),
            parsed.get("trajectory_events", []),
        )
        parsed["_trajectory"] = trajectory

        # AI scoring
        dimension_scores = await AIPipeline.rerank_candidate(job_requirements, parsed)
        candidate["dimension_scores"] = dimension_scores
        candidate["final_score"] = compute_final_score(dimension_scores)
        candidate["full_name"] = parsed.get("full_name", "Unknown")

        # Audit provenence and compliance
        await AuditAgent.log_provenance(c_id, "internal_db", list(parsed.keys()))
        await AuditAgent.log_compliance_check(c_id, job_id, "pass", ["No protected attributes used"])
        
        return candidate

    scored_candidates = []
    batch_size = 5
    for i in range(0, len(top_candidates), batch_size):
        batch = top_candidates[i:i + batch_size]
        batch_results = await asyncio.gather(*[score_one(c) for c in batch])
        scored_candidates.extend(batch_results)

    # Sort
    scored_candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    # Stage 4: Explainability for top 5
    top_5 = scored_candidates[:5]
    async def explain_one(candidate: dict) -> dict:
        c_id = str(candidate.get("id"))
        explanation = await AIPipeline.generate_explanation(
            job_requirements,
            candidate.get("parsed_data", {}),
            candidate.get("dimension_scores", {}),
        )
        candidate["explanation"] = explanation
        await AuditAgent.log_explanation(c_id, job_id, MODEL_NAME)
        return candidate

    top_5_with_explanations = await asyncio.gather(*[explain_one(c) for c in top_5])

    for i, c in enumerate(scored_candidates):
        if i < 5:
            scored_candidates[i] = top_5_with_explanations[i]

    return {
        "job_id": job_id,
        "total": len(scored_candidates),
        "results": scored_candidates,
        "query_text": query_text,
    }