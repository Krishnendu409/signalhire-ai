import asyncio
from sentence_transformers import CrossEncoder

# Load model once at module level – memory-heavy but instant inference after startup
# BGE-reranker-base: 335M parameters, ~200-300ms for 100 pairs on CPU
_reranker_model: CrossEncoder | None = None
_reranker_warmed = False

def _get_model() -> CrossEncoder:
    global _reranker_model
    if _reranker_model is None:
        _reranker_model = CrossEncoder(
            "BAAI/bge-reranker-base",
            max_length=512,
        )
    return _reranker_model


def warmup_reranker() -> None:
    """Load and warm up the cross-encoder so first user request stays fast."""
    global _reranker_warmed
    if _reranker_warmed:
        return
    model = _get_model()
    model.predict([["warmup query", "warmup document"]])
    _reranker_warmed = True


def _candidate_to_text(candidate: dict) -> str:
    """Convert parsed candidate data into a dense text representation for the cross-encoder."""
    parts = []
    
    if candidate.get("summary"):
        parts.append(candidate["summary"])
    
    if candidate.get("current_title"):
        parts.append(f"Current: {candidate['current_title']}")
    
    # Skills with high confidence
    skills = candidate.get("skills", [])
    high_conf_skills = []
    for s in skills:
        if s.get("confidence", 0) < 0.6 or s.get("negated") or s.get("excluded_from_scoring"):
            continue
        skill_name = s.get("canonical_name") or s.get("name")
        if skill_name:
            high_conf_skills.append(skill_name)
    if high_conf_skills:
        parts.append("Skills: " + ", ".join(high_conf_skills))
    
    # Recent experience titles
    experiences = candidate.get("experiences", [])
    if experiences:
        recent_titles = [exp.get("title", "") for exp in experiences[:3]]
        parts.append("Recent roles: " + " → ".join(recent_titles))
    
    # Projects
    projects = candidate.get("projects", [])
    if projects:
        project_techs = []
        for p in projects[:3]:
            project_techs.extend(p.get("technologies", []))
        if project_techs:
            parts.append("Project tech: " + ", ".join(set(project_techs[:10])))
    
    return ". ".join(parts)


async def rerank_with_cross_encoder(
    query: str,
    candidates: list[dict],
    top_k: int = 30,
) -> list[dict]:
    """
    Re-rank candidates using a cross-encoder for precise semantic matching.
    
    Args:
        query: The job description or search query text.
        candidates: List of dicts with at least 'id' and 'parsed_data' keys.
        top_k: Number of top candidates to return.
    
    Returns:
        Candidates sorted by cross_score descending, limited to top_k.
    """
    if not candidates:
        return []
    
    model = _get_model()
    
    # Build query-document pairs
    pairs = []
    for c in candidates:
        cand_text = _candidate_to_text(c.get("parsed_data", {}))
        pairs.append([query, cand_text])
    
    # Run inference in a thread pool to avoid blocking the event loop
    loop = asyncio.get_running_loop()
    scores = await loop.run_in_executor(None, lambda: model.predict(pairs))
    
    # Attach scores and sort
    for i, c in enumerate(candidates):
        c["cross_score"] = float(scores[i])
    
    candidates.sort(key=lambda x: x.get("cross_score", 0), reverse=True)
    
    return candidates[:top_k]