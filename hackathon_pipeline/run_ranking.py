"""
Deterministic JD-relative ranking pipeline for the Redrob "Senior AI Engineer" challenge.

Pipeline
--------
1. Hybrid retrieval  : precomputed MiniLM candidate embeddings (dense cosine) fused with a
                       TF-IDF/BM25 lexical score via Reciprocal Rank Fusion (RRF, k=60) to form
                       the candidate set. No network at rank time — the JD embedding is loaded
                       from a precomputed jd_embedding.npy (built by offline_embedder.py).
2. Feature extraction: JD-relative fit + universal quality + behavioural availability + JD
                       penalties (feature_extractor.extract_recruiter_features).
3. Integrity gate    : detect_honeypots() hard-flags impossible profiles; they are pushed below
                       every legitimate candidate so the top-100 honeypot rate is ~0.
4. Scoring           : transparent, deterministic weighted sum (WEIGHTS below). Ties broken by
                       candidate_id ascending (spec requirement).
5. Output            : top-100 CSV with grounded, per-candidate reasoning (no hallucinated skills).

Runs CPU-only, no network, well under the 5-minute budget. Reproduce with:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv
"""

import json
import os
import time

import numpy as np
import pandas as pd

import jd_config
from feature_extractor import (
    extract_recruiter_features,
    get_lexical_scores,
    detect_honeypots,
)

# ---------------------------------------------------------------------------
# Scoring weights — one transparent, defensible linear model. Positive terms reward genuine
# role fit; negative terms enforce the JD's "explicitly do NOT want" list. Top-10 precision
# dominates the challenge composite (0.5*NDCG@10), so title/role fit and the rare specialist
# signal are weighted highest, and the trap penalties are large.
# ---------------------------------------------------------------------------
WEIGHTS = {
    "title_similarity":            3.0,
    "specialist_skill_bonus":      2.5,   # rare retrieval/ranking/vector skills — strong TP signal
    "semantic_sim":                2.0,   # real MiniLM cosine to the JD (incl. summary/trajectory)
    "skill_coverage":              1.5,
    "retrieval_fusion":            1.0,   # RRF of dense + lexical ranks
    "seniority_alignment":         1.0,
    "hireability_score":           1.5,   # behavioural availability (JD's #1 differentiator)
    "location_fit":                0.75,
    "startup_readiness_score":     0.5,   # product vs consulting-only
    "behavioral_reliability_score":0.5,
    "quality_score":               0.4,
    "bm25_score":                  0.4,
    # penalties (negative)
    "offdomain_title_penalty":    -4.0,   # HR/Accountant/Content-Writer keyword stuffers
    "keyword_trap_penalty":       -3.0,
    "research_only_penalty":      -2.0,
    "narrow_domain_penalty":      -1.5,   # CV/speech/robotics without NLP/IR
}
HONEYPOT_PENALTY = 100.0   # hard down-rank: guarantees honeypots sit below all legitimate rows
RRF_K = 60


def load_candidates(candidates_path):
    """Load all candidates and build the lexical corpus (headline+summary+title+skills+career)."""
    all_cands, corpus_texts = [], []
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                cand = json.loads(line)
            except json.JSONDecodeError:
                continue
            all_cands.append(cand)
            profile = cand.get("profile", {}) or {}
            skills_text = " ".join((s.get("name", "") or "")
                                   for s in (cand.get("skills", []) or []) if isinstance(s, dict))
            career_text = " ".join(((j.get("title", "") or "") + " " + (j.get("description", "") or ""))
                                   for j in (cand.get("career_history", []) or []) if isinstance(j, dict))
            corpus_texts.append(" ".join([
                profile.get("headline", "") or "",
                profile.get("summary", "") or "",
                profile.get("current_title", "") or "",
                skills_text, career_text,
            ]))
    return all_cands, corpus_texts


def _rrf(rank_array):
    """Reciprocal Rank Fusion contribution for a vector of 0-based ranks."""
    return 1.0 / (RRF_K + rank_array)


def run_pipeline(candidates_path, out_path,
                 embeddings_path="candidate_embeddings.npy",
                 ids_path="candidate_ids.npy",
                 jd_emb_path="jd_embedding.npy",
                 top_k=100, retrieve_k=6000):
    start = time.time()
    print("Starting deterministic JD-relative ranking (Senior AI Engineer)...")

    # ---- 1. Dense retrieval over precomputed embeddings (no network) --------------------
    for p in (embeddings_path, ids_path):
        if not os.path.exists(p):
            raise FileNotFoundError(f"{p} missing. Run: python offline_embedder.py --candidates {candidates_path}")
    embeddings = np.load(embeddings_path).astype(np.float32)
    candidate_ids = np.load(ids_path, allow_pickle=True)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    if os.path.exists(jd_emb_path):
        jd_emb = np.load(jd_emb_path).astype(np.float32)
    else:  # documented fallback (needs the local model once); precompute is the supported path
        print("jd_embedding.npy not found — encoding JD locally (requires the MiniLM model)...")
        from sentence_transformers import SentenceTransformer
        jd_emb = SentenceTransformer("all-MiniLM-L6-v2").encode([jd_config.JD_EMBED_TEXT])[0]
    jd_emb = jd_emb / (np.linalg.norm(jd_emb) + 1e-9)

    similarities = embeddings.dot(jd_emb)
    sem_order = np.argsort(similarities)[::-1]                       # best-first
    sem_rank = np.empty(len(similarities), dtype=np.int64)
    sem_rank[sem_order] = np.arange(len(similarities))
    cid_to_sim = {candidate_ids[i]: float(similarities[i]) for i in range(len(candidate_ids))}
    cid_to_semrank = {candidate_ids[i]: int(sem_rank[i]) for i in range(len(candidate_ids))}

    # ---- 2. Lexical (BM25/TF-IDF) over the full corpus ----------------------------------
    print("Loading candidates and computing lexical relevance...")
    all_cands, corpus_texts = load_candidates(candidates_path)
    bm25_all = get_lexical_scores(jd_config.JD_EMBED_TEXT, corpus_texts)
    bm25_order = np.argsort(bm25_all)[::-1]
    bm25_rank = np.empty(len(bm25_all), dtype=np.int64)
    bm25_rank[bm25_order] = np.arange(len(bm25_all))
    cid_list = [c["candidate_id"] for c in all_cands]
    cid_to_bm25 = {cid_list[i]: float(bm25_all[i]) for i in range(len(cid_list))}
    cid_to_bmrank = {cid_list[i]: int(bm25_rank[i]) for i in range(len(cid_list))}

    # ---- 3. Hybrid candidate set via RRF (dense ∪ lexical, fused by rank) ----------------
    rrf_score = {}
    for cid in cid_list:
        sr = cid_to_semrank.get(cid, len(cid_list))
        br = cid_to_bmrank.get(cid, len(cid_list))
        rrf_score[cid] = float(_rrf(np.array(sr)) + _rrf(np.array(br)))
    retrieved = sorted(cid_list, key=lambda c: rrf_score[c], reverse=True)[:retrieve_k]
    retrieved_set = set(retrieved)
    top_records = [c for c in all_cands if c["candidate_id"] in retrieved_set]
    df = pd.DataFrame(top_records).reset_index(drop=True)
    print(f"Hybrid retrieval (RRF k={RRF_K}) -> {len(df)} candidates re-ranked.")

    # ---- 4. Feature extraction + integrity gate -----------------------------------------
    print("Extracting JD-relative, behavioural and integrity features...")
    feats = extract_recruiter_features(df, jd_config.JD_CONFIG)
    feats["candidate_id"] = df["candidate_id"].values
    is_hp, hp_reason = detect_honeypots(df)
    feats["is_honeypot"] = is_hp.values

    cids = df["candidate_id"].values
    # overwrite proxy retrieval features with the real scores
    feats["semantic_sim"] = np.clip([cid_to_sim.get(c, 0.0) for c in cids], 0, 1)
    bm25_p99 = np.percentile(bm25_all, 99) + 1e-9
    feats["bm25_score"] = np.clip([cid_to_bm25.get(c, 0.0) / bm25_p99 for c in cids], 0, 1)
    rrf_vals = np.array([rrf_score.get(c, 0.0) for c in cids])
    rrf_min, rrf_max = rrf_vals.min(), rrf_vals.max()
    feats["retrieval_fusion"] = (rrf_vals - rrf_min) / (rrf_max - rrf_min + 1e-9)

    # ---- 5. Deterministic weighted scoring ----------------------------------------------
    print("Scoring...")
    score = np.zeros(len(feats))
    for col, w in WEIGHTS.items():
        score += w * feats[col].to_numpy(dtype=float)
    score -= HONEYPOT_PENALTY * feats["is_honeypot"].to_numpy(dtype=float)
    feats["score"] = score

    # select the top-k by raw score (candidate_id asc as first tie-break)
    ranked = feats.sort_values(by=["score", "candidate_id"], ascending=[False, True]).head(top_k).copy()

    # normalise to the [0,1] display score and round to the 4 decimals that go to the CSV, then
    # re-sort by the ROUNDED score so the spec's tie-break (equal displayed score -> candidate_id
    # ascending) matches exactly what the validator checks.
    raw = ranked["score"].to_numpy()
    lo, hi = raw.min(), raw.max()
    disp = (raw - lo) / (hi - lo) if hi > lo else np.full_like(raw, 0.5)
    ranked["score"] = np.round(disp, 4)
    ranked = ranked.sort_values(by=["score", "candidate_id"], ascending=[False, True]).copy()
    ranked["rank"] = range(1, len(ranked) + 1)

    # ---- 6. Grounded reasoning ----------------------------------------------------------
    id_to_cand = {c["candidate_id"]: c for c in top_records}
    reasonings = []
    for i, (_, r) in enumerate(ranked.iterrows()):
        reasonings.append(_reason(id_to_cand[r["candidate_id"]], r, i))
    ranked["reasoning"] = reasonings

    out = ranked[["candidate_id", "rank", "score", "reasoning"]].copy()
    out["score"] = out["score"].map(lambda x: f"{x:.4f}")
    out.to_csv(out_path, index=False)
    print(f"Done in {time.time() - start:.1f}s -> {out_path} ({len(out)} rows). "
          f"Honeypots in top-100: {int(ranked['is_honeypot'].sum())}")
    return out


# ---------------------------------------------------------------------------
# Reasoning: specific, honest, varied — and never mentions a skill the candidate lacks.
# ---------------------------------------------------------------------------
_OPENERS = [
    "{title} with {yrs:.1f} yrs' experience",
    "{yrs:.1f}-year {title}",
    "{title} ({yrs:.1f} yrs)",
    "Experienced {title}, {yrs:.1f} yrs",
]


def _reason(cand, r, idx):
    profile = cand.get("profile", {}) or {}
    signals = cand.get("redrob_signals", {}) or {}
    title = (profile.get("current_title") or "professional").strip()
    yrs = float(r.get("years_of_experience", 0) or 0)

    # real skills that are relevant to this JD (from the candidate's ACTUAL skill list)
    rel_terms = [t.lower() for t in (jd_config.SPECIALIST_SKILLS + jd_config.REQ_SKILLS)]
    named = []
    for s in cand.get("skills", []) or []:
        nm = (s.get("name") or "").strip()
        if nm and any(t in nm.lower() for t in rel_terms) and nm not in named:
            named.append(nm)
    skills_clause = ""
    if named:
        skills_clause = " Relevant skills: " + ", ".join(named[:4]) + "."

    parts = [_OPENERS[idx % len(_OPENERS)].format(title=title, yrs=yrs) + "."]
    if r.get("specialist_skill_bonus", 0) >= 0.66 and r.get("title_similarity", 0) >= 0.5:
        parts.append("Strong retrieval/ranking profile matching the AI-engineer JD.")
    elif r.get("title_similarity", 0) >= 0.5:
        parts.append("Role and title align with the JD.")
    elif r.get("specialist_skill_bonus", 0) >= 0.66:
        parts.append("Carries the specialist retrieval/ML skills the JD asks for despite an adjacent title.")
    parts.append(skills_clause.strip())

    # behavioural facts (real numbers)
    rr = signals.get("recruiter_response_rate")
    notice = signals.get("notice_period_days")
    beh = []
    if rr is not None:
        beh.append(f"{rr:.0%} recruiter response")
    if signals.get("open_to_work_flag"):
        beh.append("open to work")
    if notice is not None:
        beh.append(f"{notice}d notice")
    if beh:
        parts.append("Signals: " + ", ".join(beh) + ".")

    # one honest concern where warranted
    concern = _concern(cand, r, signals, profile)
    if concern:
        parts.append(concern)

    return " ".join(p for p in parts if p).strip()


def _concern(cand, r, signals, profile):
    if r.get("narrow_domain_penalty", 0) > 0:
        return "Concern: background looks primarily computer-vision/speech with limited NLP/IR."
    if r.get("offdomain_title_penalty", 0) > 0:
        return "Concern: current title is off-domain; included on adjacent signals only."
    if r.get("research_only_penalty", 0) > 0:
        return "Concern: research-heavy profile with little production/product signal."
    rr = signals.get("recruiter_response_rate", 1.0) or 0.0
    if rr < 0.2:
        return f"Concern: low recruiter response rate ({rr:.0%}) — availability risk."
    if r.get("location_fit", 1.0) <= 0.6 and not signals.get("willing_to_relocate"):
        return f"Concern: based in {profile.get('location','abroad')}, outside India and not marked willing to relocate."
    notice = signals.get("notice_period_days", 0) or 0
    if notice >= 90:
        return f"Concern: long notice period ({notice} days)."
    yrs = float(r.get("years_of_experience", 0) or 0)
    if yrs < jd_config.SENIORITY_MIN:
        return f"Concern: {yrs:.1f} yrs is below the 5-9 year target band."
    return ""


if __name__ == "__main__":
    # default paths for a direct `python run_ranking.py` invocation from the pipeline dir
    cands = "../candidates.jsonl" if os.path.exists("../candidates.jsonl") else "candidates.jsonl"
    run_pipeline(cands, "submission.csv")
