from datetime import datetime
import re

MIN_TENURE_YEARS = 0.08
FAST_CLIMBER_PROMOTION_RATE = 0.45
FAST_CLIMBER_ALT_PROMOTION_RATE = 0.3
FAST_CLIMBER_MIN_TENURE = 1.2
STABLE_MIN_TENURE = 3.0
STABLE_MAX_TENURE = 5.5
STABLE_MAX_DIVERSITY = 0.65
HOPPER_MAX_TENURE = 2.0
HOPPER_MIN_DIVERSITY = 0.7
HOPPER_MIN_COMPANIES = 3


def _normalize_date_text(date_str: str | None) -> str:
    return re.sub(r"[,\.\(\)]", "", (date_str or "").strip().lower())


def parse_date(date_str: str) -> datetime | None:
    """Attempt to parse various date formats. Returns None on failure."""
    if not date_str:
        return None

    normalized = _normalize_date_text(date_str)
    if _is_current_role(normalized):
        return datetime.now()

    if " to " in normalized:
        normalized = normalized.split(" to ")[-1].strip()
    if " - " in normalized:
        normalized = normalized.split(" - ")[-1].strip()
    elif "-" in normalized and normalized.count("-") == 1 and " " in normalized:
        normalized = normalized.split("-")[-1].strip()

    if _is_current_role(normalized):
        return datetime.now()

    formats = [
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
        "%b %Y",
        "%B %Y",
        "%b %d %Y",
        "%B %d %Y",
        "%m/%Y",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def _is_current_role(end_date: str | None) -> bool:
    if not end_date:
        return True
    normalized = _normalize_date_text(end_date)
    current_tokens = {"present", "current", "now", "till date", "to date", "ongoing", "today", "till now"}
    return normalized in current_tokens or any(token in normalized for token in current_tokens)


def _experience_label(exp: dict) -> str:
    title = exp.get("title", "").strip()
    company = exp.get("company", "").strip()
    if title and company:
        return f"{title} at {company}"
    return title or company or "recent role"


def classify_trajectory(
    career_history: list[dict],
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
    if not career_history:
        return {
            "archetype": "unknown",
            "score": 0.5,
            "details": "No experience data available",
        }

    now = datetime.now()
    # Calculate total career span and per-role tenures
    start_dates = []
    end_dates = []
    tenures = []
    for exp in career_history:
        sd = parse_date(exp.get("start_date", ""))
        raw_end = exp.get("end_date", "")
        ed = parse_date(raw_end)
        if sd and (ed is None) and _is_current_role(raw_end):
            ed = now
        if sd:
            start_dates.append(sd)
        if ed:
            end_dates.append(ed)
        if sd and ed:
            # Prevent zero-duration artifacts when month/year-only dates collapse to same day.
            tenure_years = max(MIN_TENURE_YEARS, (ed - sd).days / 365.25)
            tenures.append(tenure_years)

    if not start_dates:
        return {
            "archetype": "unknown",
            "score": 0.5,
            "details": "Could not parse dates from experiences",
        }

    career_start = min(start_dates)
    career_end = max(end_dates) if end_dates else now
    career_years = max(0.5, (career_end - career_start).days / 365.25)

    # Count jobs and average tenure
    num_jobs = len(career_history)
    avg_tenure_years = (sum(tenures) / len(tenures)) if tenures else (career_years / max(1, num_jobs))

    # Count promotions from trajectory_events
    promotions = [e for e in trajectory_events if e.get("type") == "promotion"]
    promotion_rate = len(promotions) / career_years

    # Count lateral moves / industry switches
    lateral_moves = [e for e in trajectory_events if e.get("type") == "lateral"]
    lateral_rate = len(lateral_moves) / career_years

    # Detect industry patterns
    companies = [exp.get("company", "").strip().lower() for exp in career_history if exp.get("company")]
    unique_companies = len(set(companies))
    industries = {
        exp.get("industry", "").strip().lower()
        for exp in career_history
        if exp.get("industry")
    }
    if industries:
        industry_diversity = min(1.0, len(industries) / max(1, num_jobs))
    else:
        industry_diversity = min(1.0, unique_companies / max(1, num_jobs))

    history_snippet = ", then ".join(_experience_label(exp) for exp in career_history[:2])
    history_snippet = history_snippet or "role progression across past experience"

    # Classification logic
    if promotion_rate >= FAST_CLIMBER_PROMOTION_RATE or (
        promotion_rate >= FAST_CLIMBER_ALT_PROMOTION_RATE and avg_tenure_years >= FAST_CLIMBER_MIN_TENURE
    ):
        archetype = "fast_climber"
        score = min(1.0, 0.7 + (promotion_rate / 2))
        details = (
            f"Fast Climber: {len(promotions)} promotions over {career_years:.1f} years "
            f"({promotion_rate:.2f}/yr), including {history_snippet}."
        )
    elif STABLE_MIN_TENURE <= avg_tenure_years <= STABLE_MAX_TENURE and industry_diversity <= STABLE_MAX_DIVERSITY:
        archetype = "stable_performer"
        score = 0.9
        details = (
            f"Stable Performer: Average tenure is {avg_tenure_years:.1f} years with focused depth "
            f"(industry diversity {industry_diversity:.2f}); track includes {history_snippet}."
        )
    elif (
        avg_tenure_years < HOPPER_MAX_TENURE
        and industry_diversity >= HOPPER_MIN_DIVERSITY
        and unique_companies >= HOPPER_MIN_COMPANIES
    ):
        archetype = "chaotic_hopper"
        score = 0.4
        details = (
            f"Chaotic Hopper: Short average tenure ({avg_tenure_years:.1f} years) across "
            f"{unique_companies} companies and broad switching ({industry_diversity:.2f}); "
            f"history shows {history_snippet}."
        )
    else:
        archetype = "mixed"
        score = 0.6
        details = (
            f"Mixed trajectory: {career_years:.1f} years and {num_jobs} roles with promotion rate "
            f"{promotion_rate:.2f}/yr; progression includes {history_snippet}."
        )

    return {
        "archetype": archetype,
        "score": score,
        "details": details,
        "career_years": round(career_years, 1),
        "num_jobs": num_jobs,
        "avg_tenure": round(avg_tenure_years, 1),
        "avg_tenure_years": round(avg_tenure_years, 1),
        "promotion_rate": round(promotion_rate, 2),
        "industry_diversity": round(industry_diversity, 2),
    }