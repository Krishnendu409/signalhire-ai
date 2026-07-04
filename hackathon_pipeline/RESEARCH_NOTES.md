# Research Notes — Candidate↔JD Ranking Best Practices

Compiled to inform the pipeline rebuild and to back the Stage‑5 "defend your work" interview.
Each finding is mapped to a concrete design decision in this repo.

## 1. Hybrid retrieval + Reciprocal Rank Fusion (RRF)
- BM25 (lexical) and dense embeddings have **complementary blind spots**: BM25 nails exact/rare
  tokens (e.g. "FAISS", "Qdrant"), dense handles paraphrase/semantics (e.g. "built a recommender").
  Run both and fuse — don't pick one.
- **RRF** fuses ranked lists by rank, not raw score: `score = Σ 1/(k + rank_i)`, `k=60` by
  convention. It sidesteps the score‑incompatibility problem (BM25 0–20+ vs cosine 0–1) that breaks
  naive weighted blending.
- **Design decision:** `run_ranking.py` previously fused via ad‑hoc p99 normalization + weighted
  sum. Replaced the retrieval fusion with **RRF over the BM25 rank and the dense‑cosine rank** to
  form the candidate set / a `retrieval_fusion` feature. Cross‑encoder re‑rank is intentionally
  *not* used at inference (violates the 5‑min CPU / no‑network budget); the heuristic re‑ranker
  plays that role.
- Sources: [digitalapplied — Hybrid Search 2026](https://www.digitalapplied.com/blog/hybrid-search-bm25-vector-reranking-reference-2026),
  [Elasticsearch RRF walkthrough](https://ashutoshkumars1ngh.medium.com/hybrid-search-done-right-fixing-rag-retrieval-failures-using-bm25-hnsw-reciprocal-rank-fusion-a73596652d22),
  [Production hybrid retrieval](https://atalupadhyay.wordpress.com/2026/06/10/building-a-production-ready-hybrid-retrieval-system-from-scratch-bm25-dense-embeddings-rrf-re-ranking/).

## 2. Learning‑to‑rank (LambdaMART / LightGBM)
- LightGBM `objective='lambdarank'` directly optimizes NDCG via λ‑gradients; wants **graded
  relevance labels** and **dense engineered features**; outputs **uncalibrated scores**.
- **Design decision:** we have **no ground‑truth labels** — the existing experiment trains LGBM on
  labels bucketed from its *own* heuristic (circular) with unseeded noise (non‑deterministic). So
  the **submission is produced by the transparent, deterministic heuristic** (fully defensible at
  Stage 5), and `final_ranking_experiment.py` is kept only as a **feature‑importance / ablation
  study** — now seeded and honestly framed, not the submission source.
- Sources: [Shaped — LambdaMART explained](https://www.shaped.ai/blog/lambdamart-explained-the-workhorse-of-learning-to-rank),
  [LightGBM LTR example](https://tamaracucumides.medium.com/learning-to-rank-with-lightgbm-code-example-in-python-843bd7b44574).

## 3. Beating keyword‑stuffing (the core trap)
- Modern matching penalizes unnatural keyword repetition; repetition rarely improves rank. What
  matters is **skills embedded in career trajectory / achievements** and **only claiming what's
  true** ("keywords get you screened; actual skills get you hired").
- **Design decision:** (a) score the `summary` + career descriptions (trajectory), not just the
  skills list; (b) weight a skill by **endorsements + months used** (authenticity), so a stuffed
  skill list with 0 duration / 0 endorsements does not win; (c) explicit **off‑domain title
  penalty** (HR Manager / Accountant / Content Writer with AI keywords → down‑ranked); (d)
  honeypot integrity gate (§5).
- Sources: [Jobscan — keyword stuffing](https://www.jobscan.co/blog/resume-keyword-stuffing/),
  [EduAvenues — match without stuffing](https://www.eduavenues.com/blog/resume-keywords-ats).

## 4. Evaluation (matches the challenge's own metric)
- Rank‑aware metrics: **NDCG** (graded relevance), **MAP** (binary, top‑rank precision), **MRR**
  (first relevant), **P@K**. Challenge composite = 0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP +
  0.05·P@10 — so **top‑10 quality dominates**; optimize the head of the list hardest.
- Offline metrics correlate with each other but must be validated online (A/B) — we have no online
  loop, so we optimize the offline proxy and guard against the honeypot DQ.
- **Design decision:** keep/þextend an offline eval helper (NDCG@k/MAP/P@k) for local sanity; weight
  design toward top‑10 precision (strong title/role + integrity gate at the head).
- Sources: [Evidently — 10 ranking metrics](https://www.evidentlyai.com/ranking-metrics/evaluating-recommender-systems),
  [Weaviate — retrieval eval](https://weaviate.io/blog/retrieval-evaluation-metrics),
  [Pinecone — offline evaluation](https://www.pinecone.io/learn/offline-evaluation/).

## 5. Adversarial/anomalous profile detection (honeypots)
- No external source needed — the `submission_spec` defines them: internally inconsistent profiles
  (e.g. "expert in 10 skills with 0 years used", "8 yrs at a company founded 3 yrs ago"). Rule‑based
  integrity checks are the right tool; >10% in top‑100 = disqualification.
- **Design decision:** `detect_honeypots()` with data‑only consistency rules (expert/advanced skill
  with `duration_months==0`; tenure‑sum vs `profile.years_of_experience` divergence;
  `end_date<start_date`; `duration_months` inconsistent with the date span; `is_current` with a
  non‑null `end_date`). Flagged profiles are hard‑down‑ranked below all legitimate candidates.
