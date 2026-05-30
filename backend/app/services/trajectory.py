import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


def parse_date(date_str: str) -> datetime | None:
    """Attempt to parse various date formats. Returns None on failure."""
    if not date_str:
        return None
    normalized = date_str.strip().lower()
    normalized = re.sub(r"[()\[\],.;]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if normalized in {"present", "current", "now"} or any(
        token in normalized for token in ("present", "current", "ongoing")
    ):
        return datetime.now()
    formats = [
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
        "%b %Y",
        "%B %Y",
        "%m/%Y",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def classify_trajectory(
    experiences: list[dict],
    trajectory_events: list[dict],
) -> dict:
    """
    Classify career trajectory into archetypes:
    - fast_climber: Rapid title progression, frequent promotions, increasing scope.
    - stable_performer: Long tenures, deep expertise, steady progression.
    - chaotic_hopper: Short, unrelated stints without clear progression.
    - mixed: Characteristics of multiple archetypes.

    Returns dict with archetype, score (0-1), and supporting details.
    """
    if not experiences:
        return {
            "archetype": "unknown",
            "score": 0.5,
            "details": "No experience data available",
        }

    # Calculate total career span and per-role tenure
    start_dates = []
    end_dates = []
    tenures = []
    ongoing_role_found = False
    for exp in experiences:
        sd = parse_date(exp.get("start_date", ""))
        ed = parse_date(exp.get("end_date", ""))
        if not ed and exp.get("start_date"):
            ongoing_role_found = True
            ed = datetime.now()
        if sd:
            start_dates.append(sd)
        if ed:
            end_dates.append(ed)
        if sd and ed and ed >= sd:
            delta = relativedelta(ed, sd)
            tenure_years = delta.years + (delta.months / 12.0) + (delta.days / 365.25)
            tenures.append(max(0.0, tenure_years))

    if not start_dates:
        return {
            "archetype": "unknown",
            "score": 0.5,
            "details": "Could not parse dates from experiences",
        }

    career_start = min(start_dates)
    career_end = datetime.now() if ongoing_role_found else (max(end_dates) if end_dates else datetime.now())
    career_years = max(0.5, (career_end - career_start).days / 365.25)

    # Count jobs and average tenure
    num_jobs = len(experiences)
    avg_tenure_years = (sum(tenures) / len(tenures)) if tenures else (career_years / max(1, num_jobs))

    # Count promotions from trajectory_events
    promotions = [e for e in trajectory_events if e.get("type") == "promotion"]
    promotion_rate = len(promotions) / career_years

    # Count lateral moves / industry switches
    lateral_moves = [e for e in trajectory_events if e.get("type") == "lateral"]
    lateral_rate = len(lateral_moves) / career_years

    # Detect industry patterns
    companies = [exp.get("company", "").strip().lower() for exp in experiences if exp.get("company")]
    unique_companies = len(set(companies))
    industries = [
        (exp.get("industry") or exp.get("domain") or "").strip().lower()
        for exp in experiences
        if (exp.get("industry") or exp.get("domain"))
    ]
    industry_diversity = len(set(industries)) if industries else unique_companies
    recent_titles = [exp.get("title", "").strip() for exp in experiences[:3] if exp.get("title")]
    recent_companies = [exp.get("company", "").strip() for exp in experiences[:3] if exp.get("company")]

    # Classification logic
    if promotion_rate >= 0.5:
        archetype = "fast_climber"
        score = min(1.0, 0.7 + (promotion_rate / 2))
        details = (
            f"Promoted {len(promotions)} times in {career_years:.1f} years "
            f"({promotion_rate:.2f}/yr) with scope growth across {', '.join(recent_titles[:2]) or 'recent roles'}."
        )
    elif avg_tenure_years >= 3.5:
        archetype = "stable_performer"
        score = 0.9
        company_phrase = f" at {', '.join(recent_companies[:2])}" if recent_companies else ""
        details = (
            f"Averages {avg_tenure_years:.1f}-year tenures"
            f"{company_phrase}, signaling depth and retention."
        )
    elif avg_tenure_years <= 1.8 and industry_diversity >= 3:
        archetype = "chaotic_hopper"
        score = 0.4
        details = (
            f"Short average tenure ({avg_tenure_years:.1f} years) across {industry_diversity} industries"
            " suggests elevated retention risk."
        )
    else:
        archetype = "mixed"
        score = 0.6
        details = (
            f"Blended career arc: {num_jobs} roles over {career_years:.1f} years"
            f" with {promotion_rate:.2f}/yr promotion velocity."
        )

    return {
        "archetype": archetype,
        "score": score,
        "details": details,
        "career_years": round(career_years, 1),
        "num_jobs": num_jobs,
        "avg_tenure_years": round(avg_tenure_years, 1),
        "promotion_rate": round(promotion_rate, 2),
        "industry_diversity": industry_diversity,
    }