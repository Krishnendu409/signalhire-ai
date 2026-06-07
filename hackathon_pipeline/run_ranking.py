import os
import json
import time
import numpy as np
import pandas as pd

from feature_extractor import extract_recruiter_features, FEATURE_COLS, get_lexical_scores

def run_pipeline():
    start_time = time.time()
    print("🚀 Starting Deterministic JD-Relative Ranking Pipeline...")

    # =========================================
    # 1. LOAD OFFLINE ARTIFACTS
    # =========================================
    embeddings_path = "candidate_embeddings.npy"
    ids_path = "candidate_ids.npy"

    if not os.path.exists(embeddings_path) or not os.path.exists(ids_path):
        print(f"Error: {embeddings_path} or {ids_path} missing.")
        print("Run `python offline_embedder.py` first to precompute embeddings.")
        return

    print("Loading precomputed candidate embeddings...")
    embeddings = np.load(embeddings_path)
    candidate_ids = np.load(ids_path, allow_pickle=True)
    
    # Normalize offline embeddings if not already normalized
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    # =========================================
    # 2. CHALLENGE JD DEFINITION
    # =========================================
    # We define the challenge JD (Search Engineer) natively as a config dictionary
    jd_config = {
        'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
        'title_terms': ['search', 'machine learning', 'ai', 'ml', 'data scientist', 'backend', 'nlp', 'retrieval', 'ranking'],
        'req_skills': ['python', 'elasticsearch', 'faiss', 'machine learning'],
        'seniority_years': 5
    }
    jd_text = " ".join(jd_config['keywords'])

    print("Encoding target JD...")
    from sentence_transformers import SentenceTransformer
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception:
        print("SentenceTransformer not found. Please install: pip install sentence-transformers")
        return

    jd_emb = model.encode([jd_text])[0]
    jd_emb = jd_emb / np.linalg.norm(jd_emb)

    # =========================================
    # 3. STAGE 1: HYBRID RETRIEVAL (Top 5000)
    # =========================================
    print("Computing Semantic Similarities...")
    # Exact Cosine Similarity (O(N) CPU operation ~0.05s for 100k)
    similarities = embeddings.dot(jd_emb)

    # Top 5000 by semantic similarity
    top_k_semantic = 5000
    top_sem_indices = np.argsort(similarities)[::-1][:top_k_semantic]
    top_sem_ids = set(candidate_ids[i] for i in top_sem_indices)

    # Read ALL candidates for BM25 scoring
    print("Scanning full dataset for BM25...")
    candidates_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(candidates_path):
        candidates_path = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
        if not os.path.exists(candidates_path):
            candidates_path = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"

    all_cands = []
    corpus_texts = []

    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                cand = json.loads(line)
                all_cands.append(cand)
                # Use profile headline + summary + title + skills + career for BM25
                profile = cand.get('profile', {}) or {}
                
                # Extract skills
                skills_list = cand.get('skills', []) or []
                skills_text = " ".join([(s.get('name', '') or '') for s in skills_list if isinstance(s, dict)])
                
                # Extract career history
                career_list = cand.get('career_history', []) or []
                career_text = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in career_list if isinstance(j, dict)])
                
                text = (
                    (profile.get('headline', '') or '') + " " +
                    (profile.get('summary', '') or '') + " " +
                    (profile.get('current_title', '') or '') + " " +
                    skills_text + " " +
                    career_text
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
    # 4. STAGE 2: DYNAMIC FEATURE EXTRACTION
    # =========================================
    print("Extracting JD-Relative features...")
    features_df = extract_recruiter_features(df, jd_config)
    
    # Overwrite the approximated semantic_sim with the actual MiniLM Cosine Similarity
    features_df['semantic_sim'] = np.clip([cid_to_sim.get(cid, 0) for cid in df['candidate_id'].values], 0, 1)
    
    # Overwrite the approximated bm25 with the actual BM25 score
    bm25_p99 = np.percentile(bm25_all, 99) + 1e-9
    features_df['bm25_score'] = np.clip([cid_to_bm25.get(cid, 0) / bm25_p99 for cid in df['candidate_id'].values], 0, 1)

    features_df['candidate_id'] = df['candidate_id'].values

    # =========================================
    # 5. STAGE 3: DETERMINISTIC HEURISTIC SCORING
    # =========================================
    print("Applying mathematically validated heuristic weights...")
    
    # Optimal Weights from Parameter Grid Search
    w_title = 4.95
    w_sem = 2.18
    w_skill = 1.23
    w_sen = 0.88
    w_qual = 0.81
    w_bm25 = 0.62
    w_trap = -7.31

    features_df['score'] = (
        w_title * features_df['title_similarity'] +
        w_sem * features_df['semantic_sim'] +
        w_skill * features_df['skill_coverage'] +
        w_sen * features_df['seniority_alignment'] +
        w_qual * features_df['quality_score'] +
        w_bm25 * features_df['bm25_score'] +
        w_trap * features_df['keyword_trap_penalty']
    )

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

    # Normalize scores to [0, 1] range for Kaggle Submission format
    raw_scores = features_df['score'].values
    score_min = raw_scores.min()
    score_max = raw_scores.max()
    if score_max > score_min:
        normalized = (raw_scores - score_min) / (score_max - score_min)
    else:
        normalized = np.full_like(raw_scores, 0.5)
    features_df['score'] = normalized

    # Generate Dynamic JD-Relative Reasoning
    reasonings = []
    for _, row in features_df.iterrows():
        yrs = row.get('years_of_experience', 0)
        title = row.get('current_title', 'Professional')
        
        t_sim = row.get('title_similarity', 0)
        s_cov = row.get('skill_coverage', 0)
        sen_a = row.get('seniority_alignment', 0)
        q_score = row.get('quality_score', 0)

        parts = []

        # Opening: title + years
        if yrs > 0:
            parts.append(f"{title.title()} with {yrs:.1f} years of experience.")
        else:
            parts.append(f"{title.title()}.")

        # Alignment Parts
        if t_sim > 0.8:
            parts.append("Perfectly aligned job title and role history.")
        elif t_sim > 0.4:
            parts.append("Highly relevant professional background.")
            
        if s_cov > 0.8:
            parts.append(f"Possesses all core required skills (including Python, Elasticsearch, Faiss).")
        elif s_cov > 0.4:
            parts.append("Strong coverage of the required technical stack.")

        if sen_a > 0.8:
            parts.append("Matches the target seniority exactly.")
            
        if q_score > 1.0:
            parts.append("Exceptional profile completeness and verified signals.")

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
