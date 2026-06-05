import json
import time
import os
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import lightgbm as lgb
from feature_extractor import extract_recruiter_features, get_lexical_scores, FEATURE_COLS
from sentence_transformers import SentenceTransformer


def get_docx_text(path):
    """Extract plain text from a .docx file."""
    z = zipfile.ZipFile(path)
    xml_content = z.read('word/document.xml')
    z.close()
    tree = ET.XML(xml_content)
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join(
        ''.join(n.text for n in p.iter(w + 't') if n.text)
        for p in tree.iter(w + 'p')
        if any(n.text for n in p.iter(w + 't'))
    )


def run_pipeline():
    start_time = time.time()

    # =========================================
    # 1. LOAD RESOURCES
    # =========================================
    print("Loading pre-computed embeddings and models...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    if os.path.exists("candidate_embeddings.npy"):
        embeddings = np.load("candidate_embeddings.npy")
        with open("candidate_embeddings_ids.json", "r") as f:
            candidate_ids = json.load(f)
    else:
        print("ERROR: candidate_embeddings.npy not found.")
        print("Please run: python hackathon_pipeline/offline_embedder.py")
        return

    if not os.path.exists("lgbm_ranker.txt"):
        print("ERROR: lgbm_ranker.txt not found.")
        print("Please run: python hackathon_pipeline/train_lightgbm.py")
        return

    ranker = lgb.Booster(model_file="lgbm_ranker.txt")

    # =========================================
    # 2. PARSE JOB DESCRIPTION
    # =========================================
    jd_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx"
    if not os.path.exists(jd_path):
        jd_path = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx"
    jd_text = get_docx_text(jd_path)
    print(f"JD loaded: {len(jd_text)} characters")

    # =========================================
    # 3. STAGE 1: HYBRID RETRIEVAL
    # =========================================
    print("Encoding query for semantic retrieval...")
    query_emb = embedder.encode([jd_text], convert_to_numpy=True)[0].astype(np.float16)
    similarities = embeddings.dot(query_emb)

    # Top 5000 by semantic similarity
    top_k_semantic = 5000
    top_sem_indices = np.argsort(similarities)[::-1][:top_k_semantic]
    top_sem_ids = set(candidate_ids[i] for i in top_sem_indices)

    # Read ALL candidates for BM25 scoring
    print("Scanning full dataset for BM25...")
    candidates_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(candidates_path):
        candidates_path = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"

    all_cands = []
    corpus_texts = []

    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                cand = json.loads(line)
                all_cands.append(cand)
                # Use profile headline + summary for BM25
                profile = cand.get('profile', {}) or {}
                text = (
                    (profile.get('headline', '') or '') + " " +
                    (profile.get('summary', '') or '') + " " +
                    (profile.get('current_title', '') or '')
                )
                corpus_texts.append(text)
            except Exception:
                pass

    print(f"Loaded {len(all_cands)} candidates. Computing BM25...")
    bm25_all = get_lexical_scores(jd_text, corpus_texts)

    # Top 5000 by BM25
    top_bm25_indices = np.argsort(bm25_all)[::-1][:5000]
    top_bm25_ids = set(all_cands[i]['candidate_id'] for i in top_bm25_indices)

    # UNION of semantic and BM25 (hybrid retrieval)
    union_ids = top_sem_ids | top_bm25_ids
    print(f"Hybrid retrieval: {len(top_sem_ids)} semantic ∪ {len(top_bm25_ids)} BM25 = {len(union_ids)} union candidates")

    # Filter to union set
    top_records = [c for c in all_cands if c['candidate_id'] in union_ids]
    df = pd.DataFrame(top_records)

    # Map scores
    cid_to_sim = {candidate_ids[i]: float(similarities[i]) for i in range(len(similarities))}
    cid_to_bm25 = {all_cands[i]['candidate_id']: float(bm25_all[i]) for i in range(len(all_cands))}

    # =========================================
    # 4. STAGE 2: FEATURE EXTRACTION
    # =========================================
    print("Extracting recruiter features...")
    features_df = extract_recruiter_features(df)
    features_df['semantic_sim'] = [cid_to_sim.get(cid, 0) for cid in df['candidate_id'].values]
    features_df['bm25_score'] = [cid_to_bm25.get(cid, 0) for cid in df['candidate_id'].values]

    # NO hard-filtering — let LightGBM handle consistency penalties as soft signals
    # Attach candidate_id for final output
    features_df['candidate_id'] = df['candidate_id'].values

    # =========================================
    # 5. STAGE 3: LIGHTGBM INFERENCE
    # =========================================
    print("Running LightGBM LambdaRank inference...")
    X = features_df[FEATURE_COLS]
    scores = ranker.predict(X)
    features_df['score'] = scores

    # =========================================
    # 6. STAGE 4: TOP 100 + REASONING
    # =========================================
    print("Selecting Top 100 and generating explanations...")

    # Sort by score descending, then candidate_id ascending for tie-breaking
    features_df = features_df.sort_values(
        by=['score', 'candidate_id'],
        ascending=[False, True]
    ).head(100).copy()
    features_df['rank'] = range(1, 101)

    # Normalize scores to [0, 1] range
    raw_scores = features_df['score'].values
    score_min = raw_scores.min()
    score_max = raw_scores.max()
    if score_max > score_min:
        normalized = (raw_scores - score_min) / (score_max - score_min)
    else:
        normalized = np.full_like(raw_scores, 0.5)
    features_df['score'] = normalized

    # Generate recruiter-style reasoning
    reasonings = []
    for _, row in features_df.iterrows():
        yrs = row.get('years_of_experience', 0)
        title = row.get('current_title', 'Professional')
        ret = row.get('retrieval_experience_score', 0)
        rank_exp = row.get('ranking_experience_score', 0)
        vec = row.get('vector_db_score', 0)
        eval_f = row.get('evaluation_framework_score', 0)
        prod = row.get('production_ml_score', 0)
        hire = row.get('hireability_score', 0)
        startup = row.get('startup_readiness_score', 0)
        lead = row.get('leadership_score', 0)
        consistency = row.get('career_consistency_score', 0)

        parts = []

        # Opening: title + years
        if yrs > 0:
            parts.append(f"{title} with {yrs:.1f} years of experience.")
        else:
            parts.append(f"{title}.")

        # Technical alignment
        tech_parts = []
        if ret >= 2:
            tech_parts.append("retrieval systems")
        if rank_exp >= 2:
            tech_parts.append("ranking/recommendation")
        if vec >= 1:
            tech_parts.append("vector database infrastructure")
        if eval_f >= 1:
            tech_parts.append("evaluation frameworks (NDCG/MRR)")

        if tech_parts:
            parts.append("Strong background in " + ", ".join(tech_parts) + ".")
        elif ret >= 1 or rank_exp >= 1:
            parts.append("Some exposure to search and retrieval systems.")

        if prod >= 2:
            parts.append("Demonstrated ability to deploy and scale production ML systems.")

        if startup >= 2:
            parts.append("High startup readiness with cross-functional ownership.")

        if lead >= 2:
            parts.append("Leadership experience including team management and mentorship.")

        if hire >= 5:
            parts.append("Exceptional recruiter engagement and hireability signals.")
        elif hire >= 3:
            parts.append("Good recruiter engagement signals.")

        # Limitations
        limitations = []
        if consistency < 0.3:
            limitations.append("profile inconsistencies detected")
        if ret < 1 and rank_exp < 1:
            limitations.append("limited retrieval/ranking experience")
        if startup < 1:
            limitations.append("limited startup exposure")

        if limitations:
            parts.append("Limitations: " + "; ".join(limitations) + ".")

        reasonings.append(" ".join(parts))

    features_df['reasoning'] = reasonings

    # =========================================
    # 7. WRITE SUBMISSION
    # =========================================
    final_out = features_df[['candidate_id', 'rank', 'score', 'reasoning']].copy()
    final_out['score'] = final_out['score'].apply(lambda x: f"{x:.4f}")

    final_out.to_csv("submission.csv", index=False)

    elapsed = time.time() - start_time
    print(f"\n✅ Pipeline finished successfully in {elapsed:.2f} seconds!")
    print(f"Output saved to submission.csv ({len(final_out)} candidates)")


if __name__ == "__main__":
    run_pipeline()
