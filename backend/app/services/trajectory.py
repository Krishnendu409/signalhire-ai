from datetime import datetime
from dateutil.relativedelta import relativedelta


def parse_date(date_str: str) -> datetime | None:
    """Attempt to parse various date formats. Returns None on failure."""
    if not date_str:
        return None
    normalized = date_str.strip().lower()
    if normalized in {"present", "current", "now"}:
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

    # Calculate total career span
    start_dates = []
    end_dates = []
    for exp in experiences:
        sd = parse_date(exp.get("start_date", ""))
        ed = parse_date(exp.get("end_date", ""))
        if sd:
            start_dates.append(sd)
        if ed:
            end_dates.append(ed)

    if not start_dates:
        return {
            "archetype": "unknown",
            "score": 0.5,
            "details": "Could not parse dates from experiences",
        }

    career_start = min(start_dates)
    career_end = max(end_dates) if end_dates else datetime.now()
    career_years = max(0.5, (career_end - career_start).days / 365.25)

    # Count jobs and average tenure
    num_jobs = len(experiences)
    avg_tenure_years = career_years / num_jobs

    # Count promotions from trajectory_events
    promotions = [e for e in trajectory_events if e.get("type") == "promotion"]
    promotion_rate = len(promotions) / career_years

    # Count lateral moves / industry switches
    lateral_moves = [e for e in trajectory_events if e.get("type") == "lateral"]
    lateral_rate = len(lateral_moves) / career_years

    # Detect industry patterns
    companies = [exp.get("company", "").strip().lower() for exp in experiences if exp.get("company")]
    unique_companies = len(set(companies))

    # Classification logic
    if promotion_rate >= 0.5:
        archetype = "fast_climber"
        score = min(1.0, 0.7 + (promotion_rate / 2))
        details = f"Fast Climber: {len(promotions)} promotions in {career_years:.1f} years ({promotion_rate:.2f}/yr). High growth momentum."
    elif avg_tenure_years >= 3.5:
        archetype = "stable_performer"
        score = 0.9
        details = f"Stable Performer: Solid tenure averaging {avg_tenure_years:.1f} years. Deep institutional knowledge and commitment."
    elif avg_tenure_years <= 1.8 and unique_companies >= 3:
        archetype = "chaotic_hopper"
        score = 0.4
        details = f"Chaotic Hopper: High mobility across {unique_companies} different companies in {career_years:.1f} years. Potential retention risk."
    else:
        archetype = "mixed"
        score = 0.6
        details = f"Mixed trajectory: {career_years:.1f} years, {num_jobs} roles, showing varied professional growth patterns."

    return {
        "archetype": archetype,
        "score": score,
        "details": details,
        "career_years": round(career_years, 1),
        "num_jobs": num_jobs,
        "avg_tenure_years": round(avg_tenure_years, 1),
        "promotion_rate": round(promotion_rate, 2),
    }