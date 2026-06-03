import json
import os
from difflib import get_close_matches
from collections import defaultdict

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

_SECTION_CONFIDENCE = {
    "certification": 1.0,
    "experience": 0.8,
    "projects": 0.6,
    "education": 0.5,
    "skills": 0.2,
}


def _normalized_section(raw_section: str | None) -> str:
    section = (raw_section or "").strip().lower()
    if section in {"certification", "certifications"}:
        return "certification"
    if section in {"project", "projects"}:
        return "projects"
    if section in {"skill", "skills", "skills_list"}:
        return "skills"
    if section in {"experience", "work_experience", "employment"}:
        return "experience"
    if section in {"education", "academic"}:
        return "education"
    return "skills"


def _compute_confidence(skill: dict) -> float:
    if skill.get("negated", False):
        return 0.0
    section = _normalized_section(skill.get("source_section"))
    context = (skill.get("context") or "").lower()
    if "familiar with" in context or "basic knowledge" in context:
        return 0.3
    return _SECTION_CONFIDENCE.get(section, 0.2)


def _compound_confidence(confidences: list[float]) -> float:
    if not confidences:
        return 0.0
    product_remaining = 1.0
    for c in confidences:
        product_remaining *= max(0.0, 1.0 - c)
    return round(min(1.0, 1.0 - product_remaining), 2)


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
    Normalizes raw skills, applies section-aware confidence calibration,
    merges duplicates across sections, and marks negated skills so they
    can be excluded from scoring/embedding.
    """
    if not raw_skills:
        return []

    enriched = []
    for skill in raw_skills:
        match = normalize_skill(skill.get("name", ""))
        section = _normalized_section(skill.get("source_section"))
        negated = bool(skill.get("negated", False))
        confidence = _compute_confidence({**skill, "source_section": section, "negated": negated})
        skill["source_section"] = section
        skill["negated"] = negated
        skill["confidence"] = confidence
        if match:
            skill["canonical_name"] = match["canonical_name"]
            skill["category"] = match["category"]
            skill["match_metadata"] = match
        else:
            skill["canonical_name"] = skill.get("name", "")
            skill["category"] = "uncategorized"
            skill["match_metadata"] = {"matched_by": "none"}
        enriched.append(skill)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for skill in enriched:
        grouped[skill.get("canonical_name", skill.get("name", "")).lower()].append(skill)

    normalized = []
    for _, mentions in grouped.items():
        representative = max(mentions, key=lambda s: s.get("confidence", 0.0))
        positive_confidences = [m.get("confidence", 0.0) for m in mentions if not m.get("negated", False)]
        compounded_confidence = _compound_confidence(positive_confidences)
        sections = sorted({m.get("source_section", "skills") for m in mentions})
        negated_mentions = [m for m in mentions if m.get("negated", False)]
        all_negated = len(negated_mentions) == len(mentions)

        normalized.append({
            "name": representative.get("name", ""),
            "type": representative.get("type", "hard"),
            "canonical_name": representative.get("canonical_name", representative.get("name", "")),
            "category": representative.get("category", "uncategorized"),
            "source_section": representative.get("source_section", "skills"),
            "source_sections": sections,
            "confidence": 0.0 if all_negated else compounded_confidence,
            "context": representative.get("context", ""),
            "negated": all_negated,
            "negated_mentions": len(negated_mentions),
            "is_scoring_eligible": not all_negated and compounded_confidence > 0,
            "match_metadata": representative.get("match_metadata", {"matched_by": "none"}),
            "mentions": [
                {
                    "context": m.get("context", ""),
                    "source_section": m.get("source_section", "skills"),
                    "confidence": m.get("confidence", 0.0),
                    "negated": bool(m.get("negated", False)),
                }
                for m in mentions
            ],
        })
    return normalized