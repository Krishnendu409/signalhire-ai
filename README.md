<div align="center">
  
# 🎯 SignalHire AI: Redrob Intelligent Candidate Discovery
**Modeling Recruiter Judgment through 5 Dimensions of Technical and Behavioral Fit**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.6.0-green.svg)](https://lightgbm.readthedocs.io/)
[![Sentence Transformers](https://img.shields.io/badge/Sentence_Transformers-5.5.1-yellow.svg)](https://sbert.net/)
[![Next.js](https://img.shields.io/badge/Next.js-UI-black.svg)](https://nextjs.org/)

</div>

---

## 🚀 Overview

**SignalHire AI** is a cutting-edge retrieval and ranking pipeline built specifically for the *Redrob Intelligent Candidate Discovery & Ranking Challenge*. 

Instead of relying purely on semantic similarity—which is highly vulnerable to keyword stuffing and honeypot profiles—SignalHire AI explicitly models **Recruiter Judgment** through five dimensions:
1. **Technical Fit** (Retrieval, Ranking, Vector DBs, Evaluation)
2. **Startup Readiness** (Ownership, Cross-functional experience)
3. **Candidate Authenticity** (LLM-Artifact Detection, Multi-Profile Consistency)
4. **Hireability** (Response rates, Notice periods, Recency)
5. **Behavioral Reliability** (Role Progression Slope, Leadership momentum)

The system is designed strictly for offline, CPU-constrained execution, maintaining full forensic dataset scanning within the 5-minute wall-clock limit.

---

## ✨ Key Features & Architecture

### 🛡️ 1. Dataset Forensics & Consistency Engine
We don't just match keywords; we detect deception.
*   **Identity Consistency Score:** Cross-references headlines, summaries, and career history to find contradictions.
*   **Timeline Integrity:** Validates mathematical discrepancies between stated years of experience and actual chronologies.
*   **LLM Synthetic Generation Artifacts:** Identifies generated honeypots using a statistical penalty for known LLM-isms (e.g., *"delve"*, *"tapestry"*).
*   **Skill Inflation Penalty:** Penalizes profiles listing 50+ "Expert" skills with low actual experience.

### 🧠 2. JD-Specific Alignment Scoring
We built 16 handcrafted recruiter heuristics precisely mapped to the JD:
*   `retrieval_experience_score`
*   `ranking_experience_score`
*   `vector_db_score`
*   `evaluation_framework_score`
*   `production_ml_score`

*Mentions in current roles are mathematically weighted higher than mentions 10 years ago.*

### ⚡ 3. Hybrid Retrieval Funnel
To ensure zero high-quality candidates fall through the cracks, we use a massive union strategy:
*   **Top 5,000 via Semantic Similarity** (`all-MiniLM-L6-v2`)
*   **Top 5,000 via Lexical BM25** (TF-IDF approximation)
*   **Heavy Feature Extraction** runs on the deduplicated 10,000 candidate union.

### 🎯 4. Deterministic LightGBM LambdaRank
Instead of training our Ranker on generic pseudo-labels, we train LightGBM `lambdarank` against our **Handcrafted Recruiter Score** ground truth. This forces the model to learn the critical, non-linear interactions between technical capability and candidate authenticity.

### 💬 5. SHAP-Inspired NLG Reasoning
Explanations are generated dynamically by reading the extremity of the underlying feature vectors for each candidate.
*   *Example Output:* `"Extensive background building retrieval and ranking systems with production vector-search infrastructure. Exceptional recruiter engagement signals and hireability."*

---

## 🛠️ Execution & Pipeline

The entire system is decoupled into an offline embedding stage and a highly optimized online inference stage.

### 1. Offline Setup
To halve memory requirements and satisfy the 16GB limit, embeddings are pre-computed in `float16`.
```bash
# Generate candidate_embeddings.npy
python hackathon_pipeline/offline_embedder.py

# Train LightGBM LambdaRank model on the candidate pool
python hackathon_pipeline/train_lightgbm.py
```

### 2. Online Inference (The 5-Minute Challenge)
Run the finalized online pipeline. It loads the `float16` matrix, runs the Hybrid BM25/Semantic retrieval, runs dataset forensics, and ranks the Top 100 candidates.
```bash
# Outputs submission.csv
python hackathon_pipeline/run_ranking.py
```

---

## 💻 Tech Stack
*   **Machine Learning:** `LightGBM` (LambdaRank), `Sentence-Transformers` (`all-MiniLM-L6-v2`), `scikit-learn` (TF-IDF).
*   **Data Processing:** `pandas`, `numpy`
*   **Frontend UI:** `Next.js`, `TypeScript`, `Tailwind CSS` (Premium Glassmorphism Aesthetics)

---
<div align="center">
<i>Built to find the safe business investment.</i>
</div>
