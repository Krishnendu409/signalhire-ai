import json
import os
import re
from difflib import get_close_matches

# Load taxonomy file on module import
_TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "skill_taxonomy.json")
with open(_TAXONOMY_PATH) as f:
    TAXONOMY: dict = json.load(f)
# TAXONOMY format:
# {
#   "Canonical Skill Name": {
#     "aliases": ["alias1", "alias2"],
#     "category": "Programming Languages / Frameworks / Cloud / ..."
#   },
#   ...
# }

# Precompute flat list of all aliases for fuzzy matching
_ALL_ALIASES: dict = {}  # alias_lower -> canonical_name
for canon_name, data in TAXONOMY.items():
    _ALL_ALIASES[canon_name.lower()] = canon_name
    for alias in data.get("aliases", []):
        _ALL_ALIASES[alias.lower()] = canon_name


def normalize_skill(raw_name: str) -> dict | None:
    """Map a raw skill string to its canonical form. Returns None if no match found."""
    name_lower = raw_name.strip().lower()
    if not name_lower:
        return None

    # 1. Exact match on canonical or alias
    if name_lower in _ALL_ALIASES:
        canon = _ALL_ALIASES[name_lower]
        return {
            "raw": raw_name,
            "canonical_name": canon,
            "category": TAXONOMY[canon]["category"],
            "matched_by": "exact",
        }

    # 2. Fuzzy match on all known strings (lower threshold)
    all_keys = list(_ALL_ALIASES.keys())
    matches = get_close_matches(name_lower, all_keys, n=1, cutoff=0.75)
    if matches:
        canon = _ALL_ALIASES[matches[0]]
        return {
            "raw": raw_name,
            "canonical_name": canon,
            "category": TAXONOMY[canon]["category"],
            "matched_by": "fuzzy",
        }

    # 3. Token overlap check (e.g., "React.js" in "React")
    name_tokens = set(name_lower.split())
    for key in all_keys:
        key_tokens = set(key.split())
        # Check if one is a subset of another (simple version)
        if name_tokens.issubset(key_tokens) or key_tokens.issubset(name_tokens):
             canon = _ALL_ALIASES[key]
             return {
                "raw": raw_name,
                "canonical_name": canon,
                "category": TAXONOMY[canon]["category"],
                "matched_by": "token_overlap",
            }

    # 4. No match — return as-is with uncategorized
    return {
        "raw": raw_name,
        "canonical_name": raw_name,
        "category": "uncategorized",
        "matched_by": "none",
    }


def normalize_skills(raw_skills: list[dict]) -> list[dict]:
    """
    Normalize, calibrate, and aggregate extracted skills.
    - Applies section-aware confidence weights.
    - Detects and preserves negated skills with confidence=0.
    - Boosts confidence when a skill appears across multiple sections.
    """
    SECTION_WEIGHTS = {
        "certification": 1.0,
        "certifications": 1.0,
        "experience": 0.8,
        "projects": 0.6,
        "project": 0.6,
        "education": 0.5,
        "skills": 0.2,
        "skill": 0.2,
    }
    SOFT_SIGNAL_PATTERN = re.compile(r"\b(familiar with|basic knowledge|beginner|learning)\b", re.IGNORECASE)
    NEGATION_PATTERN = re.compile(r"\b(no experience with|have not worked with|not worked with|without)\b", re.IGNORECASE)

    grouped: dict[str, dict] = {}

    def _safe_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    for skill in raw_skills:
        match = normalize_skill(skill.get("name", ""))
        if not match:
            continue

        source_section = str(skill.get("source_section", "skills")).strip().lower()
        context = str(skill.get("context", "")).strip()
        base_confidence = _safe_float(skill.get("confidence", 0.0))
        section_confidence = SECTION_WEIGHTS.get(source_section, base_confidence or 0.2)
        calibrated_confidence = section_confidence

        if SOFT_SIGNAL_PATTERN.search(context):
            calibrated_confidence = min(calibrated_confidence, 0.3)

        explicit_negated = bool(skill.get("negated"))
        context_negated = bool(NEGATION_PATTERN.search(context))
        negated = explicit_negated or context_negated
        if negated:
            calibrated_confidence = 0.0

        canonical_name = match["canonical_name"]
        entry = grouped.setdefault(
            canonical_name,
            {
                "name": canonical_name,
                "type": skill.get("type", "hard"),
                "canonical_name": canonical_name,
                "category": match["category"],
                "match_metadata": match,
                "source_sections": set(),
                "raw_mentions": [],
                "contexts": [],
                "confidences": [],
                "negated_mentions": 0,
                "positive_mentions": 0,
            },
        )

        entry["source_sections"].add(source_section)
        entry["raw_mentions"].append(skill.get("name", ""))
        if context:
            entry["contexts"].append(context)
        entry["confidences"].append(calibrated_confidence)
        if negated:
            entry["negated_mentions"] += 1
        else:
            entry["positive_mentions"] += 1

    normalized = []
    for entry in grouped.values():
        section_count = len(entry["source_sections"])
        max_confidence = max(entry["confidences"]) if entry["confidences"] else 0.0
        boosted_confidence = min(1.0, max_confidence + max(0, section_count - 1) * 0.15)
        final_negated = entry["positive_mentions"] == 0 and entry["negated_mentions"] > 0
        final_confidence = 0.0 if final_negated else round(boosted_confidence, 2)

        normalized.append(
            {
                "name": entry["name"],
                "type": entry["type"],
                "confidence": final_confidence,
                "source_section": "multiple" if section_count > 1 else (next(iter(entry["source_sections"]), "skills")),
                "source_sections": sorted(s for s in entry["source_sections"] if s),
                "context": " | ".join(entry["contexts"][:3]),
                "negated": final_negated,
                "excluded_from_scoring": final_negated or final_confidence <= 0.0,
                "raw_mentions": entry["raw_mentions"],
                "canonical_name": entry["canonical_name"],
                "category": entry["category"],
                "match_metadata": entry["match_metadata"],
            }
        )

    return normalized