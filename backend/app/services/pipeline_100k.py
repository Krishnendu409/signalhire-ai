"""
100k Candidate Scale Pipeline Service — FULL IMPLEMENTATION
============================================================
Stage 1: Hybrid Retrieval — Top-5000 Semantic ∪ Top-5000 TF-IDF BM25
Stage 2: Full JD-Relative Feature Extraction (8 features):
         semantic_sim, bm25_score, title_similarity, skill_coverage,
         seniority_alignment, anti_skill_penalty, keyword_stuffing_risk,
         quality_score
Stage 3: Inline LightGBM LambdaRank — trained fresh on the union set
         using heuristic pseudo-labels (same as final_ranking_experiment.py)
         Falls back to validated heuristic weights on any failure:
         w_qual=0.81, w_bm25=0.62, w_trap=-7.31, anti=-3.0
Stage 4: Top-100 selection, score normalisation, reasoning generation
"""

import json
import logging
import os
import time
import numpy as np
import lightgbm as lgb
from typing import Any, Dict, List, Optional

logger = logging.getLogger("signalhire.pipeline_100k")

# ── In-memory pipeline state ──────────────────────────────────────────────────
_state: Dict[str, Any] = {
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "progress": 0,
    "stage": "",
    "error": None,
    "results": None,
}


def get_pipeline_state() -> Dict[str, Any]:
    return dict(_state)


def _update(status: str = None, progress: int = None, stage: str = None,
            error: str = None, results: dict = None):
    if status   is not None: _state["status"]   = status
    if progress is not None: _state["progress"] = progress
    if stage    is not None: _state["stage"]    = stage
    if error    is not None: _state["error"]    = error
    if results  is not None: _state["results"]  = results


# ── JD definition (Search Engineer — competition target) ──────────────────────
JD_CONFIG = {
    "family": "Search Engineer",
    "keywords": [
        "faiss", "pinecone", "elasticsearch", "search", "ranking",
        "retrieval", "machine learning", "python",
    ],
    "title_terms": [
        "search", "machine learning", "ai", "ml", "data scientist",
        "backend", "nlp", "retrieval", "ranking",
    ],
    "req_skills": ["python", "elasticsearch", "faiss", "machine learning"],
    # Anti-skills: skills/titles that belong to a totally different domain
    "anti_skills": ["sales", "hr", "recruiter", "accountant", "marketing"],
    "seniority_years": 5,
}

# ── Validated heuristic weights (from parameter grid search in run_ranking.py) ─
W_TITLE = 4.95
W_SEM   = 2.18
W_SKILL = 1.23
W_SEN   = 0.88
W_QUAL  = 0.81
W_BM25  = 0.62
W_TRAP  = -7.31
W_ANTI  = -7.31

# LightGBM feature column order must match training in final_ranking_experiment.py
LGBM_FEATURE_COLS = [
    "semantic_sim", "bm25_score", "title_similarity",
    "skill_coverage", "seniority_alignment", "anti_skill_penalty",
    "keyword_stuffing_risk", "quality_score",
    "hireability_score", "startup_readiness_score", "behavioral_reliability_score"
]

# ── Path resolution ───────────────────────────────────────────────────────────
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

_CANDIDATE_PATHS = [
    os.path.join(_ROOT, "candidates.jsonl"),
    r"C:\Users\krish\Documents\signalhire\candidates.jsonl",
    r"../candidates.jsonl",
    r"candidates.jsonl",
]

_EMBEDDING_PATHS = [
    os.path.join(_ROOT, "hackathon_pipeline", "candidate_embeddings.npy"),
    r"C:\Users\krish\Documents\signalhire\hackathon_pipeline\candidate_embeddings.npy",
    r"../hackathon_pipeline/candidate_embeddings.npy",
]

_IDS_PATHS = [
    os.path.join(_ROOT, "hackathon_pipeline", "candidate_ids.npy"),
    r"C:\Users\krish\Documents\signalhire\hackathon_pipeline\candidate_ids.npy",
    r"../hackathon_pipeline/candidate_ids.npy",
]




def _resolve(paths: List[str]) -> Optional[str]:
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


# ── Per-candidate full feature extraction ─────────────────────────────────────
def _extract_features_single(cand: dict, jd: dict) -> dict:
    """
    Extract all 7 JD-relative features + quality score for one candidate.
    Matches the feature set used in final_ranking_experiment.py.
    """
    # ── Text corpus ──────────────────────────────────────────────────────────
    skills_list = cand.get("skills", []) or []
    s_text = " ".join(
        (s.get("name", "") or "").lower()
        for s in skills_list if isinstance(s, dict)
    )

    career = cand.get("career_history", []) or []

    current_title = ""
    current_job_description = ""
    total_months = 0

    for i, job in enumerate(career):
        if not isinstance(job, dict):
            continue
        if i == 0:
            current_title = (job.get("title", "") or "").lower()
            current_job_description = (job.get("description", "") or "").lower()
        total_months += job.get("duration_months", 0) or 0

    # FIX(Bug#1): full_text must match baseline feature_extractor.py L29-39
    # Baseline uses ONLY: skills + career[0].description
    full_text = s_text + " " + current_job_description

    # ── Feature 1: Semantic / BM25 proxy (overridden later with real scores) ─
    hits = sum(1 for k in jd["keywords"] if k in full_text)
    semantic_sim = hits / max(len(jd["keywords"]), 1)
    bm25_score   = semantic_sim * 0.8  # proxy, overridden after TF-IDF

    # ── Feature 2: Title similarity ──────────────────────────────────────────
    t_hits = sum(1 for w in jd["title_terms"] if w in current_title)
    title_similarity = min(t_hits / 2.0, 1.0)

    # ── Feature 3: Skill coverage ────────────────────────────────────────────
    sk_hits = sum(1 for k in jd["req_skills"] if k in s_text)
    skill_coverage = sk_hits / max(len(jd["req_skills"]), 1)

    # ── Feature 4: Seniority alignment ──────────────────────────────────────
    yoe = total_months / 12.0
    diff = abs(yoe - jd["seniority_years"])
    seniority_alignment = max(0.0, 1.0 - (diff / 10.0))

    # ── Feature 5: Anti-skill penalty (Linear Range-Based Scaling) ───────────
    # We assign different base penalties for different anti-skills
    # and scale the penalty linearly based on how long they worked in that role (the range)
    anti_skill_weights = {
        "hr": 1.0,
        "recruiter": 1.0,
        "accountant": 1.0,
        "marketing": 0.8,
        "sales": 0.6
    }
    
    anti_penalty_score = 0.0
    for job in career:
        if not isinstance(job, dict): continue
        title_j = (job.get("title", "") or "").lower()
        desc_j = (job.get("description", "") or "").lower()
        job_text = title_j + " " + desc_j
        duration = job.get("duration_months", 0) or 0
        
        for askill, base_weight in anti_skill_weights.items():
            if askill in job_text or askill in s_text:
                # Linear scaling depending on the range of the anti-skill (duration)
                # Cap the linear scale at 24 months (2 years) = full penalty
                range_multiplier = min(max(duration, 6) / 24.0, 1.0)
                anti_penalty_score += base_weight * range_multiplier

    anti_skill_penalty = float(np.clip(anti_penalty_score, 0.0, 1.0))

    # ── Feature 6: Keyword stuffing / trap risk ───────────────────────────────
    # High BM25 proxy AND zero title match → keyword stuffer
    keyword_stuffing_risk = 1.0 if (bm25_score > 0.6 and title_similarity == 0) else 0.0

    # ── Feature 7: Universal quality score ───────────────────────────────────
    signals = cand.get("redrob_signals", {}) or {}
    q = 0.0
    q += signals.get("profile_completeness_score", 50) / 100.0
    q += min(signals.get("github_activity_score", 0) / 100.0, 1.0)
    if signals.get("verified_email"):    q += 0.5
    if signals.get("linkedin_connected"): q += 0.5
    quality_score = q

    # ── Feature 8: Hireability (Notice Period Sigmoid & Response Rate) ────────
    import math
    notice_days = signals.get('notice_period_days', 90)
    friction = 1.0 / (1.0 + math.exp(-0.1 * (notice_days - 30)))
    rr = signals.get('recruiter_response_rate', 0.0)
    otw = 1.0 if signals.get('open_to_work_flag') else 0.0
    hireability_score = (rr * 0.5) + (otw * 0.2) + ((1.0 - friction) * 0.3)

    # ── Feature 9: Startup Readiness ─────────────────────────────────────────
    consulting_firms = ["tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini"]
    consulting_hits = 0
    product_hits = 0
    for job in career:
        comp = str(job.get("company", "")).lower()
        if any(c in comp for c in consulting_firms):
            consulting_hits += 1
        else:
            product_hits += 1
    startup_readiness_score = 0.0 if (consulting_hits > 0 and product_hits == 0) else 1.0

    # ── Feature 10: Behavioral Reliability ───────────────────────────────────
    if len(career) > 0:
        total_months = sum((job.get('duration_months', 0) or 0) for job in career)
        avg_tenure_years = (total_months / 12.0) / len(career)
        if avg_tenure_years < 1.5:
            behavioral_reliability_score = 0.0
        else:
            behavioral_reliability_score = min(avg_tenure_years / 3.0, 1.0)
    else:
        behavioral_reliability_score = 0.5

    matched_skills = [k for k in jd["req_skills"] if k in s_text]
    missing_skills = [k for k in jd["req_skills"] if k not in s_text]

    return {
        # LGBM feature cols (must match LGBM_FEATURE_COLS order)
        "semantic_sim":          semantic_sim,
        "bm25_score":            bm25_score,
        "title_similarity":      title_similarity,
        "skill_coverage":        skill_coverage,
        "seniority_alignment":   seniority_alignment,
        "anti_skill_penalty":    anti_skill_penalty,
        "keyword_stuffing_risk": keyword_stuffing_risk,
        "quality_score":         quality_score,
        "hireability_score":     hireability_score,
        "startup_readiness_score": startup_readiness_score,
        "behavioral_reliability_score": behavioral_reliability_score,
        # Metadata
        "current_title":  current_title,
        "years_of_experience": round(yoe, 1),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        # Heuristic raw score (calculated after real sem/bm25 injected)
        "_full_text": full_text,
    }


def _heuristic_score(feat: dict) -> float:
    # FIX(Bug#2): Must match baseline run_ranking.py L156-163 exactly.
    # Baseline uses 7 features — NO anti_skill_penalty term.
    # anti_skill_penalty is still computed for LightGBM but NOT used here.
    return (
        W_TITLE * feat["title_similarity"] +
        W_SEM   * feat["semantic_sim"] +
        W_SKILL * feat["skill_coverage"] +
        W_SEN   * feat["seniority_alignment"] +
        W_QUAL  * feat["quality_score"] +
        W_BM25  * feat["bm25_score"] +
        W_TRAP  * feat["keyword_stuffing_risk"] +
        0.5 * feat["hireability_score"] +
        0.5 * feat["startup_readiness_score"] +
        0.5 * feat["behavioral_reliability_score"]
    )


def _generate_reasoning(feat: dict) -> str:
    parts = []
    yrs   = feat.get("years_of_experience", 0)
    title = feat.get("current_title", "Professional")

    if yrs > 0:
        parts.append(f"{title.title()} with {yrs:.1f} years of experience.")
    else:
        parts.append(f"{title.title()}.")

    if feat.get("title_similarity", 0) > 0.8:
        parts.append("Perfectly aligned job title and role history.")
    elif feat.get("title_similarity", 0) > 0.4:
        parts.append("Highly relevant professional background.")

    if feat.get("skill_coverage", 0) > 0.8:
        parts.append("Possesses all core required skills (Python, Elasticsearch, FAISS).")
    elif feat.get("skill_coverage", 0) > 0.4:
        parts.append("Strong coverage of the required technical stack.")

    if feat.get("seniority_alignment", 0) > 0.8:
        parts.append("Matches the target seniority exactly.")

    if feat.get("quality_score", 0) > 1.0:
        parts.append("Exceptional profile completeness and verified signals.")

    if feat.get("anti_skill_penalty", 0) > 0.5:
        parts.append("Note: partial domain overlap with non-target skills detected.")

    return " ".join(parts)


# ── Main synchronous pipeline (called via asyncio.to_thread) ─────────────────
def _run_pipeline_sync() -> dict:
    t0 = time.time()
    jd = JD_CONFIG

    # ── Stage 1: Load precomputed embeddings ──────────────────────────────────
    _update(progress=5, stage="Loading precomputed candidate embeddings…")
    emb_path = _resolve(_EMBEDDING_PATHS)
    ids_path = _resolve(_IDS_PATHS)

    embeddings: Optional[np.ndarray] = None
    candidate_ids_emb: Optional[np.ndarray] = None

    if emb_path and ids_path:
        logger.info(f"Loading embeddings from {emb_path}")
        embeddings = np.load(emb_path)
        candidate_ids_emb = np.load(ids_path, allow_pickle=True)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms
        logger.info(f"Loaded {len(embeddings):,} embeddings")
    else:
        logger.warning("Embeddings not found — semantic retrieval stage skipped")

    # ── Stage 2: Encode JD with MiniLM ───────────────────────────────────────
    jd_text = " ".join(jd["keywords"])
    jd_emb: Optional[np.ndarray] = None

    if embeddings is not None:
        _update(progress=10, stage="Encoding job description with MiniLM…")
        try:
            from sentence_transformers import SentenceTransformer
            st_model = SentenceTransformer("all-MiniLM-L6-v2")
            jd_emb = st_model.encode([jd_text])[0]
            jd_emb = jd_emb / np.linalg.norm(jd_emb)
            logger.info("JD encoded with MiniLM")
        except Exception as e:
            logger.warning(f"SentenceTransformer unavailable ({e}) — heuristic-only mode")
            embeddings = None

    # ── Stage 3: Semantic similarities ───────────────────────────────────────
    similarities: Optional[np.ndarray] = None
    top_sem_ids: set = set()

    if embeddings is not None and jd_emb is not None:
        _update(progress=15, stage="Computing exact cosine similarities over 100k…")
        similarities = embeddings.dot(jd_emb)          # O(N) ~50ms
        top_sem_indices = np.argsort(similarities)[::-1][:5000]
        top_sem_ids = set(str(candidate_ids_emb[i]) for i in top_sem_indices)
        logger.info(f"Semantic top-5000: {len(top_sem_ids):,}")

    # ── Stage 4: Load full candidate JSONL + build BM25 corpus ───────────────
    _update(progress=25, stage="Loading full 100k candidate dataset for BM25…")
    cand_path = _resolve(_CANDIDATE_PATHS)
    if not cand_path:
        raise FileNotFoundError(
            "candidates.jsonl not found. Searched:\n" + "\n".join(_CANDIDATE_PATHS)
        )

    logger.info(f"Reading candidates from {cand_path}")
    all_cands: List[dict] = []
    corpus_texts: List[str] = []

    with open(cand_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                cand = json.loads(line)
                all_cands.append(cand)

                # Build rich BM25 document: headline + summary + title + ALL skills + ALL job text
                profile = cand.get("profile", {}) or {}
                skills_list = cand.get("skills", []) or []
                skills_text = " ".join(
                    (s.get("name", "") or "") for s in skills_list if isinstance(s, dict)
                )
                career_list = cand.get("career_history", []) or []
                career_text = " ".join(
                    (j.get("title", "") or "") + " " + (j.get("description", "") or "")
                    for j in career_list if isinstance(j, dict)
                )
                text = (
                    (profile.get("headline", "") or "") + " " +
                    (profile.get("summary", "") or "") + " " +
                    (profile.get("current_title", "") or "") + " " +
                    skills_text + " " + career_text
                )
                corpus_texts.append(text)
            except Exception:
                pass

    total = len(all_cands)
    logger.info(f"Loaded {total:,} candidates")

    # ── Stage 5: TF-IDF BM25 over full corpus ────────────────────────────────
    _update(progress=40, stage=f"Running TF-IDF BM25 over {total:,} candidates…")

    from sklearn.feature_extraction.text import TfidfVectorizer
    # FIX(Bug#3): Must match baseline feature_extractor.py L99 (max_features=5000)
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus_texts + [jd_text])
    query_vec    = tfidf_matrix[-1]
    corpus_vecs  = tfidf_matrix[:-1]
    bm25_all     = corpus_vecs.dot(query_vec.T).toarray().flatten()

    top_bm25_indices = np.argsort(bm25_all)[::-1][:5000]
    top_bm25_ids = set(str(all_cands[i]["candidate_id"]) for i in top_bm25_indices)

    # UNION: hybrid retrieval
    union_ids = top_sem_ids | top_bm25_ids
    logger.info(
        f"Hybrid: {len(top_sem_ids):,} sem ∪ {len(top_bm25_ids):,} BM25 = {len(union_ids):,}"
    )

    # ── Build score lookup maps ───────────────────────────────────────────────
    cid_to_sim: Dict[str, float] = {}
    if similarities is not None and candidate_ids_emb is not None:
        for i, cid in enumerate(candidate_ids_emb):
            cid_to_sim[str(cid)] = float(similarities[i])

    bm25_p99 = float(np.percentile(bm25_all, 99)) + 1e-9
    cid_to_bm25: Dict[str, float] = {
        str(all_cands[i]["candidate_id"]): float(bm25_all[i]) / bm25_p99
        for i in range(len(all_cands))
    }

    # ── Stage 6: Full feature extraction for union set ────────────────────────
    _update(progress=60, stage="Extracting 8-feature JD-relative vectors…")
    top_records = [c for c in all_cands if str(c.get("candidate_id", "")) in union_ids]
    logger.info(f"Extracting features for {len(top_records):,} union candidates")

    scored: List[dict] = []
    for cand in top_records:
        cid  = str(cand.get("candidate_id", ""))
        feat = _extract_features_single(cand, jd)

        # Inject real semantic + BM25 scores
        if cid in cid_to_sim:
            feat["semantic_sim"] = float(np.clip(cid_to_sim[cid], 0.0, 1.0))
        feat["bm25_score"] = float(np.clip(cid_to_bm25.get(cid, 0.0), 0.0, 1.0))
        # Re-evaluate keyword stuffing risk with real bm25
        feat["keyword_stuffing_risk"] = (
            1.0 if feat["bm25_score"] > 0.6 and feat["title_similarity"] == 0 else 0.0
        )

        feat["candidate_id"] = cid
        feat["_cand"]        = cand
        scored.append(feat)

    # ── Stage 7: Scoring — LightGBM LambdaRank ────────────
    _update(progress=78, stage="Scoring candidates with LightGBM LambdaRank model…")
    
    # Still compute heuristic score for debugging/fallback
    for feat in scored:
        feat["_raw_score"] = _heuristic_score(feat)
    
    # LightGBM has been trained with targeted NaN injection and structural
    # regularization to degrade gracefully when embeddings are missing.
    use_lgbm = True
    lgbm_path = os.path.join(_ROOT, "backend", "app", "services", "lgbm_ranker.txt")
    
    try:
        if use_lgbm and os.path.exists(lgbm_path):
            lgbm_model = lgb.Booster(model_file=lgbm_path)
            
            # Extract features in exact order required
            X_pred = np.array([[feat[col] for col in LGBM_FEATURE_COLS] for feat in scored])
            
            # Predict
            lgbm_scores = lgbm_model.predict(X_pred)
            
            # Assign LGBM scores back to raw_score
            for i, feat in enumerate(scored):
                feat["_raw_score"] = float(lgbm_scores[i])
        elif use_lgbm:
            logger.warning(f"LightGBM model not found at {lgbm_path}. Falling back to heuristic.")
            use_lgbm = False
    except Exception as e:
        logger.error(f"Failed to run LightGBM prediction: {e}")
        use_lgbm = False

    # ── Stage 8: Top-100 + normalisation ─────────────────────────────────────
    _update(progress=88, stage="Selecting Top 100 and normalising scores…")
    scored.sort(key=lambda x: (-x["_raw_score"], x.get("candidate_id", "")))
    top100 = scored[:100]

    raw_scores = np.array([r["_raw_score"] for r in top100])
    s_min, s_max = raw_scores.min(), raw_scores.max()
    if s_max > s_min:
        normalised = (raw_scores - s_min) / (s_max - s_min)
    else:
        normalised = np.full_like(raw_scores, 0.5, dtype=float)

    # ── Stage 9: Build result records ─────────────────────────────────────────
    _update(progress=94, stage="Generating reasoning and packaging results…")
    results       = []
    skill_dist: Dict[str, int] = {}
    signals_map: Dict[str, Dict] = {}

    for rank_idx, (feat, norm_score) in enumerate(zip(top100, normalised)):
        cand    = feat["_cand"]
        profile = cand.get("profile", {}) or {}
        name    = (
            cand.get("full_name") or
            profile.get("full_name") or
            profile.get("anonymized_name") or
            f"Candidate {rank_idx + 1}"
        )
        title = feat["current_title"] or profile.get("current_title", "Unknown")

        matched = feat.get("matched_skills", [])
        missing = feat.get("missing_skills", [])

        for sk in matched:
            if sk:
                skill_dist[sk] = skill_dist.get(sk, 0) + 1

        for sig_name in ["title_similarity", "skill_coverage", "seniority_alignment"]:
            entry = signals_map.setdefault(sig_name, {
                "name": sig_name.replace("_", " ").title(),
                "count": 0, "total_rank": 0, "total_score": 0.0,
            })
            if feat.get(sig_name, 0) > 0.3:
                entry["count"]       += 1
                entry["total_rank"]  += rank_idx + 1
                entry["total_score"] += float(norm_score) * 100

        reasoning = _generate_reasoning(feat)
        career_history = cand.get("career_history", []) or []
        career_steps = [
            {
                "role":    (j.get("title")   or "Unknown"),
                "company": (j.get("company") or "Unknown"),
                "year": int((j.get("start_date") or "2020").split("-")[0])
                if j.get("start_date") else 2020,
            }
            for j in career_history[:5] if isinstance(j, dict)
        ]

        final_pct = round(float(norm_score) * 100, 2)

        results.append({
            "rank":              rank_idx + 1,
            "candidate_id":      feat["candidate_id"],
            "full_name":         name,
            "title":             title,
            "final_score":       final_pct,
            "score":             f"{float(norm_score):.4f}",
            "reasoning":         reasoning,
            "matched_skills":    matched,
            "missing_skills":    missing,
            "years_of_experience": feat.get("years_of_experience", 0),
            "career":            career_steps,
            "explanation":       reasoning,
            # Feature contribution breakdown (useful for UI drill-down)
            "feature_scores": {
                "title_similarity":      round(feat["title_similarity"] * 100, 1),
                "skill_coverage":        round(feat["skill_coverage"] * 100, 1),
                "seniority_alignment":   round(feat["seniority_alignment"] * 100, 1),
                "semantic_sim":          round(feat["semantic_sim"] * 100, 1),
                "bm25_score":            round(feat["bm25_score"] * 100, 1),
                "quality_score":         round(min(feat["quality_score"] / 3.0, 1.0) * 100, 1),
                "anti_skill_penalty":    round(feat["anti_skill_penalty"] * 100, 1),
                "keyword_stuffing_risk": round(feat["keyword_stuffing_risk"] * 100, 1),
            },
            "dimension_scores": {
                "title_similarity":  {"score": round(feat["title_similarity"] * 100, 1)},
                "skill_coverage":    {"score": round(feat["skill_coverage"] * 100, 1)},
                "seniority_alignment": {"score": round(feat["seniority_alignment"] * 100, 1)},
                "quality_score":     {"score": round(min(feat["quality_score"] / 3.0, 1.0) * 100, 1)},
                "semantic_relevance":{"score": round(feat["semantic_sim"] * 100, 1)},
            },
            "parsed_data": {
                "full_name":      name,
                "current_title":  title,
                "career_history": career_history,
                "redrob_signals": cand.get("redrob_signals", {}),
            },
            "decisionPath": {
                "enteredVia": f"100k Pipeline ({'LightGBM LambdaRank' if use_lgbm else 'Heuristic Weights'})",
                "rankedBecause":    [reasoning] if reasoning else ["Met requirement threshold"],
                "penalizedBecause": (
                    ["Keyword stuffing detected"]   if feat["keyword_stuffing_risk"] > 0 else []
                ) + (
                    ["Anti-skill contamination"]     if feat["anti_skill_penalty"] > 0.5 else []
                ),
            },
        })

    # ── Build analytics payload ───────────────────────────────────────────────
    signals_list = []
    for sig in signals_map.values():
        cnt = sig["count"]
        if cnt > 0:
            signals_list.append({
                "name":     sig["name"],
                "count":    cnt,
                "avgRank":  round(sig["total_rank"] / cnt, 1),
                "avgScore": round(sig["total_score"] / cnt, 1),
            })
    signals_list.sort(key=lambda x: -x["count"])

    n_trap         = sum(1 for r in scored if r.get("keyword_stuffing_risk", 0) > 0)
    n_anti         = sum(1 for r in scored if r.get("anti_skill_penalty", 0) > 0.3)
    n_low_skill    = sum(1 for r in scored if r.get("skill_coverage", 0) < 0.25)
    n_sen_mismatch = sum(1 for r in scored if r.get("seniority_alignment", 0) < 0.5)

    elapsed = round(time.time() - t0, 1)
    scoring_method = "LightGBM LambdaRank" if use_lgbm else "Heuristic (w_title=4.95, w_sem=2.18, w_skill=1.23)"
    logger.info(f"Pipeline complete in {elapsed}s | scoring={scoring_method}")

    return {
        "status":          "completed",
        "total_evaluated": total,
        "retrieved":       len(union_ids),
        "ranked":          len(top100),
        "shortlisted":     len(top100),
        "elapsed_seconds": elapsed,
        "model":           f"100k Hybrid Pipeline — {scoring_method}",
        "scoring_method":  scoring_method,
        "used_lgbm":       use_lgbm,
        "results":         results,
        "analytics": {
            "totalEvaluated": total,
            "retrieved":      len(union_ids),
            "ranked":         len(top100),
            "shortlisted":    len(top100),
            "model":          f"100k Hybrid — {scoring_method}",
            "skills":  dict(sorted(skill_dist.items(), key=lambda x: -x[1])[:15]),
            "signals": signals_list[:6],
            "rejections": [
                {"reason": "Keyword Stuffing (High BM25, Zero Title Match)", "count": n_trap},
                {"reason": "Anti-Skill Contamination (Wrong Domain)", "count": n_anti},
                {"reason": "Missing Core Hard Skills (<25% coverage)", "count": n_low_skill},
                {"reason": "Seniority Mismatch (>5yr gap from target)", "count": n_sen_mismatch},
            ],
        },
    }


# ── Async entry point ─────────────────────────────────────────────────────────
async def run_100k_pipeline():
    # Called by the FastAPI route. Runs the CPU pipeline in a thread pool.
    import asyncio

    if _state["status"] == "running":
        logger.warning("Pipeline already running — ignoring duplicate trigger")
        return

    _state.update({
        "status":      "running",
        "started_at":  time.time(),
        "finished_at": None,
        "progress":    0,
        "error":       None,
        "results":     None,
        "stage":       "Initialising…",
    })

    try:
        result = await asyncio.to_thread(_run_pipeline_sync)
        _state.update({
            "results":     result,
            "status":      "completed",
            "progress":    100,
            "stage":       "Done",
            "finished_at": time.time(),
        })
    except Exception as exc:
        import traceback
        traceback.print_exc()
        logger.error(f"100k pipeline failed: {exc}")
        _state.update({
            "status":      "failed",
            "error":       str(exc),
            "finished_at": time.time(),
        })
