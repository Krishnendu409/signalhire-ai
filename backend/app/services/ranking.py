import logging
from typing import Dict, Any, List
from app.services.engine import RankingEngine

logger = logging.getLogger(__name__)

# Global singleton to keep df cached in memory across requests
_engine_instance = None

def get_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RankingEngine()
    return _engine_instance

async def rank_candidates_for_job(
    job_id: str,
    job_requirements: dict,
    candidates: list[dict],
) -> dict:
    """
    Ranking wrapper that uses the frozen hackathon RankingEngine.
    This eliminates Qdrant/Postgres/SentenceTransformers overhead and uses determinism.
    """
    logger.info(f"Using RankingEngine for job_id={job_id}")
    
    # Extract query features from job_requirements
    # job_requirements comes from parse_jd_text in jobs.py
    # or it might be raw from the DB.
    
    title = job_requirements.get("title", "Search Engineer")
    req_hard = job_requirements.get("required_hard_skills", [])
    req_soft = job_requirements.get("required_soft_skills", [])
    req_skills = list(set([s.lower() for s in req_hard + req_soft]))
    
    # We map the title to family
    family = "Unknown"
    engine = get_engine()
    title_lower = title.lower()
    for fam, terms in engine.config['role_families'].items():
        if any(t.lower() in title_lower for t in terms):
            family = fam
            break
    if family == "Unknown":
        family = "Search Engineer"
        
    title_terms = engine.config['role_families'].get(family, [])
    
    jd_data = {
        "family": family,
        "keywords": req_skills,
        "title_terms": title_terms,
        "req_skills": req_skills
    }
    
    # Run the determinisitc pipeline
    results = engine.run_pipeline(jd_data, top_k=100)
    
    # Calculate total and query string
    query_text = title + " " + " ".join(req_skills)
    
    return {
        "job_id": job_id,
        "total": len(results),
        "results": results,
        "query_text": query_text,
    }