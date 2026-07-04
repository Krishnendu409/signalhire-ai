# SignalHire AI — Redrob Candidate Ranking

Ranking system for the Redrob *Intelligent Candidate Discovery & Ranking Challenge*. It ranks the
100k-candidate pool against the released **"Senior AI Engineer — Founding Team"** JD, deliberately
resisting the dataset's traps (AI-keyword stuffers, off-domain titles, ~80 impossible honeypots)
and weighing behavioural availability, as the JD requires.

## Challenge submission — reproduce the CSV

The ranking step runs **CPU-only, no network, in ~30s** (well under the 5-minute / 16 GB budget).

```bash
cd hackathon_pipeline
python -m pip install -r requirements.txt

# One-time offline precompute (embeddings need the model / may exceed 5 min — this is allowed):
python offline_embedder.py --candidates ../candidates.jsonl
#   -> writes candidate_embeddings.npy, candidate_ids.npy, jd_embedding.npy

# The single reproduce command (Stage-3): loads precomputed artifacts, no network, no GPU:
python rank.py --candidates ../candidates.jsonl --out submission.csv

# Validate before submitting:
python "../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py" submission.csv
```

### Methodology (how it beats the traps)
1. **Hybrid retrieval** — precomputed MiniLM dense embeddings (incl. each candidate's `summary`
   / career trajectory) fused with a TF-IDF/BM25 lexical score via **Reciprocal Rank Fusion**
   (`k=60`) to form the re-rank set.
2. **Transparent, deterministic scoring** (`run_ranking.WEIGHTS`) over JD-relative fit
   (title/role, a rare **retrieval/vector-DB specialist-skill** signal, semantic sim, seniority),
   **skill authenticity** (endorsements + months used, not raw keyword count), **behavioural
   availability** (recruiter response, activity recency, open-to-work, notice), **location fit**,
   and product-vs-consulting-vs-research signals.
3. **Trap/penalty terms** push down off-domain title-holders (HR Manager / Accountant / Content
   Writer with stuffed AI skills), CV/speech-only profiles, and research-only profiles.
4. **Honeypot integrity gate** (`feature_extractor.detect_honeypots`) hard-flags impossible
   profiles (expert skills with 0 months used; tenure exceeding career; date/duration
   contradictions) so the top-100 honeypot rate is **0**.
5. **Grounded reasoning** — per candidate, cites real title/YOE, only skills the candidate
   actually lists (no hallucination), real engagement numbers, and an honest concern where
   warranted; phrasing varies by rank.

`jd_config.py` is the single source of truth for the JD. `RESEARCH_NOTES.md` documents the IR/
ranking best practices behind these choices. `engine.py` re-implements the same deterministic
scoring for the interactive Next.js demo (see the root `README.md` for that product).

## Quick Start (interactive demo product)

The offline files above are the graded submission. There's also a separate full-stack demo
product (FastAPI backend + Next.js frontend) that showcases the same ranking approach
interactively — see **[the root README](../README.md#running-the-interactive-demo)** for setup,
or just run `start.bat` from the repo root on Windows.

---

## Case Study: The "Sales Manager" Contamination Fix

### The Failure Mode
During early iterations of the ranking engine, querying for a "Sales Manager" resulted in extreme title contamination. The Top 5 candidates returned were:
1. Accountant
2. HR Manager
3. Marketing Manager
4. Accountant
5. Operations Manager

A Sales Executive did not appear until Rank #14. The system was satisfying mathematical metrics but completely failing the human-review recruiter audit.

### The Root Cause
Our forensic audit revealed two primary flaws:
1. **Substring Matching:** The string `.contains("account")` matched "Accountant", `.contains("manager")` matched "HR Manager" and "Marketing Manager".
2. **Broad Role-Family Tokens:** The dictionary used broad bypass tokens such as `manager`, `executive`, and `account` mapped to the generic `Sales Manager` role family without penalizing off-domain domains.

### The Fix
We implemented two major architectural changes:
1. **Dictionary Cleanup:** Pruned the `Sales Manager` title dictionary to highly specific terms: `['sales', 'revenue', 'business development', 'gtm', 'growth', 'customer success', 'account executive', 'territory']`.
2. **Regex Word-Boundary Matching:** Upgraded the engine from basic substring matching to vectorized regex utilizing `\b` word boundaries (e.g., `\baccount\b` instead of `account`).

### Before/After Ranking Behavior
**Before:**
* Rank 1: Accountant
* Rank 2: HR Manager
* Rank 3: Marketing Manager

**After:**
* Rank 1: Sales Manager
* Rank 2: Account Executive
* Rank 3: VP of Sales
* Rank 4: Business Development Manager

**Result:** 0% honeypot penetration. The top 100 results are composed entirely of verified sales professionals while maintaining a healthy Title Entropy of 3.84 (no exact-title monoculture).

---

For the interactive demo product's API endpoints and full setup, see the [root README](../README.md).
