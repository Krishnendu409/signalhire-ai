import json
import os
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

    # 2. Fuzzy match on all known strings
    all_keys = list(_ALL_ALIASES.keys())
    matches = get_close_matches(name_lower, all_keys, n=1, cutoff=0.85)
    if matches:
        canon = _ALL_ALIASES[matches[0]]
        return {
            "raw": raw_name,
            "canonical_name": canon,
            "category": TAXONOMY[canon]["category"],
            "matched_by": "fuzzy",
        }

    # 3. No match — return as-is with uncategorized
    return {
        "raw": raw_name,
        "canonical_name": raw_name,
        "category": "uncategorized",
        "matched_by": "none",
    }


def normalize_skills(raw_skills: list[dict]) -> list[dict]:
    """
    Takes the list of skill dicts from AI resume parsing and enriches
    each with canonical_name, category, and match metadata.
    """
    normalized = []
    for skill in raw_skills:
        match = normalize_skill(skill.get("name", ""))
        if match:
            skill["canonical_name"] = match["canonical_name"]
            skill["category"] = match["category"]
            skill["match_metadata"] = match
        else:
            skill["canonical_name"] = skill.get("name", "")
            skill["category"] = "uncategorized"
            skill["match_metadata"] = {"matched_by": "none"}
        normalized.append(skill)
    return normalized