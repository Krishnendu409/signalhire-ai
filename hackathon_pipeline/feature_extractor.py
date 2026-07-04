"""
JD-relative feature extraction for the Redrob candidate-ranking pipeline.

Fixes over the previous version:
  * reads profile.summary + profile.headline + ALL career descriptions (the plain-language
    Tier-5 signal used to live only in career_history[0].description and was mostly ignored);
  * uses the authoritative profile.years_of_experience instead of double-counting overlapping
    tenures;
  * scores skill matches by AUTHENTICITY (endorsements + months used) rather than raw keyword
    hits, so a stuffed skills list with 0 duration / 0 endorsements does not win;
  * extends behavioural "hireability" with activity recency, response rate, interview
    completion, open-to-work and notice friction (the JD's #1 differentiator);
  * adds off-domain-title, research-only, narrow-domain (CV/speech/robotics) and location
    penalties/fit derived from the real JD;
  * adds detect_honeypots() — rule-based profile-integrity checks that hard-flag the
    ~80 impossible profiles so they can be pushed below every legitimate candidate.

All lists come from jd_config.py (the single source of truth). Existing column names are
preserved for backward compatibility with run_ranking.py.
"""

import math
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

import jd_config


def _lc(x):
    return (x or "").lower()


def _months_between(start, end):
    """Whole months between two 'YYYY-MM-DD' strings (end may be None -> use REFERENCE_DATE)."""
    try:
        s = datetime.strptime(start[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None
    if end:
        try:
            e = datetime.strptime(end[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return None
    else:
        e = datetime.strptime(jd_config.REFERENCE_DATE, "%Y-%m-%d")
    return (e.year - s.year) * 12 + (e.month - s.month)


def _skill_trust(skill):
    """Authenticity weight for a single skill in [0,1] from months used + endorsements.

    A matched required skill always counts a little (floor 0.25) but only genuine skills
    (used for a while, endorsed) approach 1.0 — this is the anti-keyword-stuffing lever.
    """
    dur = skill.get("duration_months", 0) or 0
    endo = skill.get("endorsements", 0) or 0
    return float(np.clip(0.25 + 0.45 * min(dur / 24.0, 1.0) + 0.30 * min(endo / 12.0, 1.0), 0.0, 1.0))


def _seniority_alignment(yoe, jd):
    """Asymmetric alignment: full credit inside the JD band, steeper penalty for too-junior,
    gentle penalty for very senior."""
    lo, hi = jd_config.SENIORITY_MIN, jd_config.SENIORITY_MAX
    if lo <= yoe <= hi:
        return 1.0
    if yoe < lo:
        return max(0.0, 1.0 - (lo - yoe) / 5.0)      # 0 by ~5 yrs below the floor
    return max(0.0, 1.0 - (yoe - hi) / 12.0)          # 0 by ~12 yrs above the ceiling


def extract_recruiter_features(df, jd_data=None):
    """Extract JD-relative + universal quality + behavioural features.

    df rows are raw candidate dicts (as loaded from candidates.jsonl). Returns a DataFrame
    indexed like df with the columns in FEATURE_COLS plus metadata columns.
    """
    if jd_data is None:
        jd_data = jd_config.JD_CONFIG

    ref = datetime.strptime(jd_config.REFERENCE_DATE, "%Y-%m-%d")
    keywords = [k.lower() for k in jd_data["keywords"]]
    title_terms = [t.lower() for t in jd_data["title_terms"]]
    req_skills = [s.lower() for s in jd_data["req_skills"]]

    features = pd.DataFrame(index=df.index)

    for idx, row in df.iterrows():
        profile = row.get("profile", {}) or {}
        career = row.get("career_history", []) or []
        skills_list = row.get("skills", []) or []
        signals = row.get("redrob_signals", {}) or {}

        # --- text corpora ---
        headline = _lc(profile.get("headline"))
        summary = _lc(profile.get("summary"))
        current_title = _lc(profile.get("current_title")) or (_lc(career[0].get("title")) if career else "")
        s_text = " ".join(_lc(s.get("name")) for s in skills_list if isinstance(s, dict))
        career_text = " ".join(
            _lc(j.get("title")) + " " + _lc(j.get("description"))
            for j in career if isinstance(j, dict)
        )
        # Plain-language career trajectory (headline + summary + all roles) — the Tier-5 signal.
        trajectory_text = " ".join([headline, summary, career_text])
        full_text = s_text + " " + trajectory_text

        # =========================================================
        # BUCKET A: Query-relative fit
        # =========================================================
        # 1. keyword-density proxy (semantic_sim / bm25 are overwritten with real scores in
        #    run_ranking.py; these are only fallbacks when embeddings are unavailable).
        hits = sum(1 for k in keywords if k in full_text)
        features.at[idx, "semantic_sim"] = hits / max(len(keywords), 1)
        features.at[idx, "bm25_score"] = features.at[idx, "semantic_sim"] * 0.8

        # 2. title similarity (word-boundary count of target-role tokens in the current title)
        t_hits = sum(1 for w in title_terms if _wb(w, current_title))
        features.at[idx, "title_similarity"] = min(t_hits / 2.0, 1.0)

        # 3. skill coverage, weighted by authenticity (endorsements + months used)
        skill_by_name = {_lc(s.get("name")): s for s in skills_list if isinstance(s, dict)}
        covered = 0.0
        for req in req_skills:
            match = next((sk for nm, sk in skill_by_name.items() if req in nm), None)
            if match is not None:
                covered += _skill_trust(match)
        features.at[idx, "skill_coverage"] = min(covered / max(len(req_skills), 1), 1.0)

        # 3b. specialist retrieval/ranking/vector-DB skills — rare, high-signal for THIS JD.
        #     Saturates at ~3 present (having a few is already a strong true-positive).
        spec_present = sum(1 for sp in jd_config.SPECIALIST_SKILLS
                           if any(sp in nm for nm in skill_by_name))
        features.at[idx, "specialist_skill_bonus"] = min(spec_present / 3.0, 1.0)

        # 4. seniority (authoritative YOE from profile; tenure-sum kept only for integrity checks)
        yoe = float(profile.get("years_of_experience") or 0.0)
        tenure_months = sum((j.get("duration_months", 0) or 0) for j in career)
        if yoe <= 0:
            yoe = tenure_months / 12.0
        features.at[idx, "seniority_alignment"] = _seniority_alignment(yoe, jd_data)

        # =========================================================
        # BUCKET B: Universal candidate quality
        # =========================================================
        q = 0.0
        q += (signals.get("profile_completeness_score", 50) / 100.0)
        q += min((signals.get("github_activity_score", 0) / 100.0), 1.0)  # -1 (no github) -> ~0
        if signals.get("verified_email"):
            q += 0.5
        if signals.get("linkedin_connected"):
            q += 0.5
        features.at[idx, "quality_score"] = q

        # =========================================================
        # BUCKET C: Behavioural availability (JD: down-weight the unhireable)
        # =========================================================
        # activity recency vs the deterministic REFERENCE_DATE
        recency = 0.5
        la = signals.get("last_active_date")
        if la:
            try:
                days = (ref - datetime.strptime(la[:10], "%Y-%m-%d")).days
                recency = float(np.clip(1.0 - max(0, days - 30) / 150.0, 0.0, 1.0))
            except (ValueError, TypeError):
                recency = 0.5
        features.at[idx, "activity_recency"] = recency

        rr = signals.get("recruiter_response_rate", 0.0) or 0.0
        icr = signals.get("interview_completion_rate", 0.0) or 0.0
        otw = 1.0 if signals.get("open_to_work_flag") else 0.0
        notice = signals.get("notice_period_days", 90)
        notice_friction = 1.0 / (1.0 + math.exp(-0.05 * (notice - 45)))     # ~0 short notice, ~1 long
        saved = min((signals.get("saved_by_recruiters_30d", 0) or 0) / 10.0, 1.0)

        hireability = (
            0.30 * rr
            + 0.20 * recency
            + 0.15 * otw
            + 0.15 * (1.0 - notice_friction)
            + 0.10 * icr
            + 0.10 * saved
        )
        features.at[idx, "hireability_score"] = float(np.clip(hireability, 0.0, 1.0))

        # startup / product readiness: consulting-only career -> 0 (JD disqualifier)
        consulting_hits = product_hits = 0
        for j in career:
            comp = _lc(j.get("company"))
            if any(c in comp for c in jd_config.CONSULTING_FIRMS):
                consulting_hits += 1
            else:
                product_hits += 1
        features.at[idx, "startup_readiness_score"] = 0.0 if (consulting_hits > 0 and product_hits == 0) else 1.0

        # behavioural reliability: average tenure (penalise <1.5y job-hoppers / title-chasers)
        if career:
            avg_tenure = (tenure_months / 12.0) / len(career)
            behavioral = 0.0 if avg_tenure < 1.5 else min(avg_tenure / 3.0, 1.0)
        else:
            behavioral = 0.5
        features.at[idx, "behavioral_reliability_score"] = behavioral

        # =========================================================
        # BUCKET D: JD penalties (from the "explicitly do NOT want" list)
        # =========================================================
        is_relevant_title = any(_wb(rt, current_title) or rt in current_title
                                for rt in jd_config.RELEVANT_TITLES)
        is_offdomain = any(od in current_title for od in jd_config.OFFDOMAIN_TITLES)
        features.at[idx, "offdomain_title_penalty"] = 1.0 if (is_offdomain and not is_relevant_title) else 0.0

        # keyword-stuffer: strong content match but off-domain / no title match
        features.at[idx, "keyword_trap_penalty"] = 1.0 if (
            features.at[idx, "semantic_sim"] > 0.25
            and (features.at[idx, "title_similarity"] == 0.0 or (is_offdomain and not is_relevant_title))
        ) else 0.0

        # research-only (no production/product signal anywhere)
        has_research = any(m in trajectory_text for m in jd_config.RESEARCH_ONLY_MARKERS)
        has_production = any(m in trajectory_text for m in jd_config.PRODUCTION_MARKERS)
        features.at[idx, "research_only_penalty"] = 1.0 if (has_research and not has_production) else 0.0

        # CV / speech / robotics primary, without NLP/IR exposure. Use word-boundary tokens so
        # "search" does not match "research" (a false NLP/IR signal).
        is_narrow = any(_wb(n, current_title) or _wb(n, full_text) for n in jd_config.NARROW_DOMAIN_TITLES)
        has_nlp_ir = any(_wb(tok, full_text) for tok in (
            "nlp", "natural language", "information retrieval", "semantic search",
            "retrieval", "ranking", "recommender", "recommendation"))
        features.at[idx, "narrow_domain_penalty"] = 1.0 if (is_narrow and not has_nlp_ir) else 0.0

        # location fit (JD: Pune/Noida preferred; India welcome; overseas needs relocation)
        loc = _lc(profile.get("location"))
        country = _lc(profile.get("country"))
        willing = bool(signals.get("willing_to_relocate"))
        if any(c in loc for c in jd_config.PREFERRED_CITIES):
            loc_fit = 1.0
        elif "india" in country or any(c in loc for c in jd_config.INDIA_CITIES):
            loc_fit = 0.85
        elif willing:
            loc_fit = 0.6
        else:
            loc_fit = 0.25
        features.at[idx, "location_fit"] = loc_fit

        # metadata
        features.at[idx, "current_title"] = current_title
        features.at[idx, "years_of_experience"] = yoe

    return features


def _wb(term, text):
    """Word-boundary containment (handles multi-word terms); avoids 'ml' matching 'html' etc."""
    import re
    return re.search(r"\b" + re.escape(term) + r"\b", text) is not None


def detect_honeypots(df):
    """Rule-based profile-integrity gate. Returns (is_honeypot: bool Series, reasons: Series[str]).

    High-confidence "impossible profile" rules (spec §7) — kept conservative so we do not
    down-rank legitimate candidates (only ~80 honeypots exist in 100k):
      H1  a job with end_date earlier than start_date
      H2  a job's stated duration_months disagrees with its start->end span by > 9 months
      H3  a single job's tenure exceeds the whole career (profile YOE*12 + 18 months slack)
      H4  >=5 skills claimed advanced/expert with duration_months == 0 ("expert, never used")
      H5  is_current true while end_date is non-null (contradiction)
    """
    flags = []
    reasons = []
    for _, row in df.iterrows():
        profile = row.get("profile", {}) or {}
        career = row.get("career_history", []) or []
        skills_list = row.get("skills", []) or []
        yoe = float(profile.get("years_of_experience") or 0.0)
        why = []

        for j in career:
            if not isinstance(j, dict):
                continue
            sd, ed = j.get("start_date"), j.get("end_date")
            dur = j.get("duration_months", 0) or 0
            span = _months_between(sd, ed)
            if span is not None and ed and span < 0:
                why.append("end_before_start")            # H1
            if span is not None and abs(dur - span) > 9:
                why.append("duration_vs_dates_mismatch")  # H2
            if yoe > 0 and dur > yoe * 12 + 18:
                why.append("tenure_exceeds_career")       # H3
            if j.get("is_current") and ed:
                why.append("current_with_end_date")       # H5

        zero_dur_expert = sum(
            1 for s in skills_list
            if isinstance(s, dict)
            and (s.get("proficiency") in ("advanced", "expert"))
            and (s.get("duration_months", 0) or 0) == 0
        )
        if zero_dur_expert >= 3:
            why.append("expert_skills_never_used")        # H4 (pool jumps 0 -> 3+, never 1-2)

        flags.append(len(why) > 0)
        reasons.append(",".join(sorted(set(why))))

    return pd.Series(flags, index=df.index), pd.Series(reasons, index=df.index)


# Columns produced by extract_recruiter_features (excluding metadata).
FEATURE_COLS = [
    "semantic_sim", "bm25_score", "title_similarity", "skill_coverage",
    "specialist_skill_bonus", "seniority_alignment", "quality_score", "keyword_trap_penalty",
    "hireability_score", "startup_readiness_score", "behavioral_reliability_score",
    "activity_recency", "offdomain_title_penalty", "research_only_penalty",
    "narrow_domain_penalty", "location_fit",
]


def get_lexical_scores(query, corpus_texts):
    """Fast BM25-style lexical relevance via TF-IDF cosine (CPU, deterministic)."""
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus_texts + [query])
    query_vec = tfidf_matrix[-1]
    corpus_vecs = tfidf_matrix[:-1]
    scores = corpus_vecs.dot(query_vec.T).toarray().flatten()
    return scores
