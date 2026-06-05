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

The system is designed strictly for offline, CPU-constrained execution, maintaining full forensic dataset scanning within the 5-minute wall-clock limit. We extract **22 recruiter-aligned features** prior to LightGBM lambda-rank scoring.

---

## 🛠️ Complete Setup Instructions (For Beginners)

If you are new to programming, don't worry! Follow these step-by-step instructions to get the AI pipeline running on your own computer.

### Step 1: Install Python
You need Python installed on your computer to run the AI models.
1. Go to the [Python Downloads Page](https://www.python.org/downloads/).
2. Download the latest version of Python (3.11 or higher is recommended).
3. **Important for Windows Users:** During the installation, make sure to check the box that says **"Add Python to PATH"** before clicking Install.

### Step 2: Download the Project
1. Open your computer's terminal (Command Prompt or PowerShell on Windows, Terminal on Mac).
2. Clone this repository to your computer by typing:
   ```bash
   git clone https://github.com/Krishnendu409/signalhire-ai.git
   ```
3. Move into the project folder:
   ```bash
   cd signalhire-ai
   ```

### Step 3: Install Required Packages
The AI relies on several external libraries (like `pandas` for data and `lightgbm` for ranking). You need to install them.
Run this command in your terminal:
```bash
pip install pandas numpy scikit-learn lightgbm sentence-transformers
```
*(Depending on your computer, you might need to use `pip3` instead of `pip`)*

### Step 4: Add the Hackathon Dataset
1. Ensure you have the hackathon dataset folder named `[PUB] India_runs_data_and_ai_challenge`.
2. Place this folder directly next to or inside the `signalhire-ai` folder so the pipeline can read `candidates.jsonl` and `job_description.docx`.

---

## 🏃 Running the AI Pipeline

The pipeline is split into two parts: an **Offline** preparation step and an **Online** ranking step.

### Part 1: Offline Preparation (Run this ONCE)
This step reads all 100,000 candidates and converts their text into mathematical vectors (embeddings), and then trains the AI model on what makes a "good" candidate.
1. In your terminal, run the embedder:
   ```bash
   python hackathon_pipeline/offline_embedder.py
   ```
   *(Note: This process reads 100,000 candidates and calculates deep AI vectors using just your CPU. It may take 1-2 hours depending on your computer's speed. Let it run until it finishes!)*
   
2. Next, train the Ranker AI model:
   ```bash
   python hackathon_pipeline/train_lightgbm.py
   ```
   *(This step takes about 1 minute. It generates a file called `lgbm_ranker.txt`)*

### Part 2: Online Ranking (The Fast Challenge)
Once the offline setup is complete, you can run the final ranking engine. This part simulates the hackathon's 5-minute constraint. It quickly searches the 100,000 candidates, extracts our 22 recruiter features, filters out fake profiles, and scores the Top 100.
1. Run the ranking script:
   ```bash
   python hackathon_pipeline/run_ranking.py
   ```
2. **Success!** Within seconds, this will generate a file named `submission.csv` in your folder. This file contains the Top 100 candidates ranked from 1 to 100, complete with scores and detailed AI-generated recruiter explanations for *why* they were chosen.

### Part 3: Running the Next.js Frontend Dashboard (Optional)
We built a beautiful frontend visualization to view your `submission.csv` results directly in the browser!
1. Install Node.js from the [Node.js Downloads Page](https://nodejs.org/).
2. In your terminal, move into the `frontend` directory:
   ```bash
   cd frontend
   ```
3. Install frontend dependencies:
   ```bash
   npm install
   ```
4. Start the dashboard:
   ```bash
   npm run dev
   ```
5. Open your web browser and go to `http://localhost:3000` to interact with the Next.js Dashboard!

---

## ✨ Key Features & Architecture Details

For technical judges, here is how the engine actually works under the hood:

### 🛡️ 1. Dataset Forensics & Consistency Engine
We don't just match keywords; we detect deception.
*   **Identity Consistency Score:** Cross-references headlines, summaries, and career history to find contradictions.
*   **Timeline Integrity:** Validates mathematical discrepancies between stated years of experience and actual chronologies.
*   **LLM Synthetic Generation Artifacts:** Identifies generated honeypots using a statistical penalty for known LLM-isms (e.g., *"delve"*, *"tapestry"*).
*   **Skill Inflation Penalty:** Penalizes profiles listing 50+ "Expert" skills with low actual experience.

### 🧠 2. JD-Specific Alignment Scoring
We built 22 handcrafted recruiter heuristics precisely mapped to the JD:
*   `retrieval_experience_score`
*   `ranking_experience_score`
*   `vector_db_score`
*   `evaluation_framework_score`
*   `production_ml_score`
*   `profile_completeness`
*   `avg_skill_assessment`
*   `trust_score`

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

<div align="center">
<i>Built to find the safe business investment.</i>
</div>
