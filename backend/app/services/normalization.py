"""
normalization.py — Production-grade skill and title normalization.

Pipeline:
  Raw extraction → exact alias match → fuzzy alias match → embedding similarity

Model: sentence-transformers/all-MiniLM-L6-v2
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_SKILL_ONTOLOGY_PATH = _DATA_DIR / "skill_ontology.json"
_TITLE_ONTOLOGY_PATH = _DATA_DIR / "title_ontology.json"

# ── Lazy-loaded globals ──────────────────────────────────────────────────────

_skill_ontology: dict | None = None
_title_ontology: dict | None = None

# Flat alias → canonical maps (built once)
_skill_alias_map: dict[str, str] = {}
_title_alias_map: dict[str, str] = {}

# Embedding model (loaded on first use)
_embed_model = None
_skill_embeddings = None        # shape (N, 384)
_skill_canonical_list: list[str] = []

_title_embeddings = None
_title_canonical_list: list[str] = []


def _load_ontologies() -> None:
    global _skill_ontology, _title_ontology
    global _skill_alias_map, _title_alias_map

    if _skill_ontology is not None:
        return  # already loaded

    try:
        with open(_SKILL_ONTOLOGY_PATH, encoding="utf-8") as f:
            _skill_ontology = json.load(f)
        with open(_TITLE_ONTOLOGY_PATH, encoding="utf-8") as f:
            _title_ontology = json.load(f)
    except FileNotFoundError as e:
        logger.warning(f"[NORM] Ontology file not found: {e}. Normalization will be no-op.")
        _skill_ontology = {}
        _title_ontology = {}
        return

    # Build alias maps (lowercase)
    for canonical, data in _skill_ontology.items():
        for alias in data.get("aliases", []):
            _skill_alias_map[alias.lower().strip()] = canonical
        # canonical itself
        _skill_alias_map[canonical.lower().strip()] = canonical

    for canonical, data in _title_ontology.items():
        for alias in data.get("aliases", []):
            _title_alias_map[alias.lower().strip()] = canonical
        _title_alias_map[canonical.lower().strip()] = canonical

    logger.info(
        f"[NORM] Loaded {len(_skill_ontology)} skills / {len(_skill_alias_map)} skill aliases | "
        f"{len(_title_ontology)} titles / {len(_title_alias_map)} title aliases"
    )


def _get_embed_model():
    return None

    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("[NORM] Loaded embedding model all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"[NORM] Could not load embedding model: {e}. Similarity fallback disabled.")
            _embed_model = False  # sentinel: failed
    return _embed_model if _embed_model is not False else None


def _build_skill_embeddings():
    global _skill_embeddings, _skill_canonical_list
    if _skill_embeddings is not None:
        return
    model = _get_embed_model()
    if model is None or not _skill_ontology:
        return
    _skill_canonical_list = list(_skill_ontology.keys())
    logger.info(f"[NORM] Building skill embeddings for {len(_skill_canonical_list)} skills…")
    _skill_embeddings = model.encode(_skill_canonical_list, normalize_embeddings=True, show_progress_bar=False)


def _build_title_embeddings():
    global _title_embeddings, _title_canonical_list
    if _title_embeddings is not None:
        return
    model = _get_embed_model()
    if model is None or not _title_ontology:
        return
    _title_canonical_list = list(_title_ontology.keys())
    logger.info(f"[NORM] Building title embeddings for {len(_title_canonical_list)} titles…")
    _title_embeddings = model.encode(_title_canonical_list, normalize_embeddings=True, show_progress_bar=False)


# ── Public API ───────────────────────────────────────────────────────────────

def normalize_skill(raw: str, sim_threshold: float = 0.82) -> dict:
    """
    Normalize a single raw skill string.
    Returns:
        {
          "name": str,               # canonical name
          "raw": str,                # original
          "match_method": str,       # "exact" | "alias" | "embedding" | "none"
          "confidence": float,       # 1.0 / 0.95 / cosine_sim
        }
    """
    _load_ontologies()
    raw_clean = raw.strip()
    lower = raw_clean.lower()

    # 1. Exact canonical match
    if raw_clean in (_skill_ontology or {}):
        return {"name": raw_clean, "raw": raw_clean, "match_method": "exact", "confidence": 1.0}

    # 2. Alias map lookup
    if lower in _skill_alias_map:
        canonical = _skill_alias_map[lower]
        return {"name": canonical, "raw": raw_clean, "match_method": "alias", "confidence": 0.97}

    # 3. Partial alias lookup (raw is substring of alias or alias is substring of raw)
    for alias, canonical in _skill_alias_map.items():
        if len(alias) >= 4 and (alias in lower or lower in alias):
            return {"name": canonical, "raw": raw_clean, "match_method": "alias_partial", "confidence": 0.88}

    # 4. Embedding similarity fallback
    model = _get_embed_model()
    if model is not None and _skill_canonical_list:
        _build_skill_embeddings()
        if _skill_embeddings is not None:
            import numpy as np
            qvec = model.encode([raw_clean], normalize_embeddings=True)[0]
            sims = _skill_embeddings @ qvec
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            if best_sim >= sim_threshold:
                return {
                    "name": _skill_canonical_list[best_idx],
                    "raw": raw_clean,
                    "match_method": "embedding",
                    "confidence": round(best_sim, 4),
                }

    # 5. No match — return raw
    return {"name": raw_clean, "raw": raw_clean, "match_method": "none", "confidence": 0.0}


def normalize_title(raw: str, sim_threshold: float = 0.82) -> dict:
    """
    Normalize a raw job title string.
    Returns:
        {
          "normalized": str,         # canonical title
          "family": str,
          "seniority": str,
          "match_method": str,
          "confidence": float,
        }
    """
    _load_ontologies()
    raw_clean = raw.strip()
    lower = raw_clean.lower()

    # 1. Exact
    if raw_clean in (_title_ontology or {}):
        meta = _title_ontology[raw_clean]
        return {"normalized": raw_clean, "family": meta.get("family", ""), "seniority": meta.get("seniority", ""), "match_method": "exact", "confidence": 1.0}

    # 2. Alias map
    if lower in _title_alias_map:
        canonical = _title_alias_map[lower]
        meta = _title_ontology.get(canonical, {})
        return {"normalized": canonical, "family": meta.get("family", ""), "seniority": meta.get("seniority", ""), "match_method": "alias", "confidence": 0.97}

    # 3. Partial alias
    for alias, canonical in _title_alias_map.items():
        if len(alias) >= 5 and alias in lower:
            meta = _title_ontology.get(canonical, {})
            return {"normalized": canonical, "family": meta.get("family", ""), "seniority": meta.get("seniority", ""), "match_method": "alias_partial", "confidence": 0.88}

    # 4. Embedding
    model = _get_embed_model()
    if model is not None and _title_canonical_list:
        _build_title_embeddings()
        if _title_embeddings is not None:
            import numpy as np
            qvec = model.encode([raw_clean], normalize_embeddings=True)[0]
            sims = _title_embeddings @ qvec
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            if best_sim >= sim_threshold:
                canonical = _title_canonical_list[best_idx]
                meta = _title_ontology.get(canonical, {})
                return {
                    "normalized": canonical,
                    "family": meta.get("family", ""),
                    "seniority": meta.get("seniority", ""),
                    "match_method": "embedding",
                    "confidence": round(best_sim, 4),
                }

    # 5. No match
    return {"normalized": raw_clean, "family": "", "seniority": "", "match_method": "none", "confidence": 0.0}


def extract_skills_from_text(text: str) -> list[dict]:
    """
    Full ontology-based skill extraction from raw resume text.
    Scans for every alias in the ontology.
    Returns list of {name, raw, evidence, match_method, confidence}.
    """
    _load_ontologies()
    if not _skill_ontology:
        return []

    found: dict[str, dict] = {}  # canonical → result dict

    SHORT_ALIASES = {
        "c", "r", "go", "js", "ts", "ui", "ux", "ml", "dl", "it", "ad", "wp",
        "tf", "np", "py", "rl", "hci", "ios", "sql", "api", "css", "aws",
        "gcp", "bq", "iac", "iam", "sre", "soc", "etl", "bi", "qa", "eda",
    }

    for canonical, data in _skill_ontology.items():
        for alias in data.get("aliases", []):
            if canonical in found:
                break
            al = alias.lower()
            if al in SHORT_ALIASES or len(al) <= 3:
                # Strict word-boundary pattern for short tokens
                pattern = r'(?:(?<=\s)|(?<=,)|(?<=\()|^)' + re.escape(al) + r'(?=\s|,|\)|$|\/)'
            else:
                pattern = r'\b' + re.escape(al) + r'\b'

            m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if m:
                # Grab up to 120 chars of surrounding context as evidence
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 90)
                snippet = text[start:end].replace('\n', ' ').strip()
                found[canonical] = {
                    "name": canonical,
                    "raw": m.group(0),
                    "evidence": snippet,
                    "match_method": "alias",
                    "confidence": 0.97,
                    "type": "hard",
                    "is_scoring_eligible": True,
                    "negated": False,
                }
                break

    return list(found.values())


def normalize_skills_list(skills: list[dict]) -> list[dict]:
    """
    Normalize a list of skill dicts (each with at least "name" key).
    Adds normalized_name, family domains, confidence.
    """
    _load_ontologies()
    result = []
    seen: set[str] = set()
    for s in skills:
        raw_name = s.get("name", "")
        norm = normalize_skill(raw_name)
        canonical = norm["name"]
        if canonical in seen:
            continue
        seen.add(canonical)
        entry = {**s, **norm}
        # Add domain info
        if canonical in (_skill_ontology or {}):
            entry["parent_domains"] = _skill_ontology[canonical].get("parent_domains", [])
            entry["related_skills"] = _skill_ontology[canonical].get("related_skills", [])
        entry["is_scoring_eligible"] = norm["confidence"] > 0.5
        entry["negated"] = False
        result.append(entry)
    return result


# Pre-warm on import (non-blocking path, embeddings built lazily)
try:
    _load_ontologies()
except Exception as e:
    logger.warning(f"[NORM] Pre-warm failed: {e}")
