import json
import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

def get_lexical_scores(query, corpus_texts):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus_texts + [query])
    query_vec = tfidf_matrix[-1]
    corpus_vecs = tfidf_matrix[:-1]
    scores = corpus_vecs.dot(query_vec.T).toarray().flatten()
    return scores

def run_ablation(jd_path, role_name):
    print(f"\n=========================================")
    print(f"RUNNING ABLATION: {role_name}")
    print(f"=========================================")
    
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    print("Loading embeddings...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = np.load("candidate_embeddings.npy")
    with open("candidate_embeddings_ids.json", "r") as f:
        candidate_ids = json.load(f)

    jd_words = jd_text.split()
    chunk_size = 200
    overlap = 50
    jd_chunks = [" ".join(jd_words[i:i + chunk_size]) for i in range(0, max(1, len(jd_words) - overlap), chunk_size - overlap) if " ".join(jd_words[i:i + chunk_size])]
    
    chunk_embs = embedder.encode(jd_chunks, convert_to_numpy=True).astype(np.float16)
    sim_matrix = embeddings.dot(chunk_embs.T)
    sorted_sims = np.sort(sim_matrix, axis=1)[:, ::-1]
    similarities = np.mean(sorted_sims[:, :5], axis=1)

    candidates_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    all_cands = []
    corpus_texts = []
    
    print("Loading text corpus...")
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                cand = json.loads(line)
                all_cands.append(cand)
                profile = cand.get('profile', {}) or {}
                skills_list = cand.get('skills', []) or []
                skills_text = " ".join([s.get('name', '') for s in skills_list if isinstance(s, dict)])
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
            except Exception: pass

    print("Computing BM25...")
    bm25_all = get_lexical_scores(jd_text, corpus_texts)

    cid_to_sim = {candidate_ids[i]: float(similarities[i]) for i in range(len(similarities))}
    cid_to_bm25 = {all_cands[i]['candidate_id']: float(bm25_all[i]) for i in range(len(all_cands))}
    
    sim_vals = np.array(list(cid_to_sim.values()))
    bm25_vals = np.array(list(cid_to_bm25.values()))
    
    sim_norm = (sim_vals - sim_vals.min()) / (sim_vals.max() - sim_vals.min() + 1e-9)
    bm25_norm = (bm25_vals - bm25_vals.min()) / (bm25_vals.max() - bm25_vals.min() + 1e-9)
    
    combined_score = (sim_norm * 0.6) + (bm25_norm * 0.4)
    
    top_indices = np.argsort(combined_score)[::-1][:20]
    
    out_lines = []
    out_lines.append(f"\n--- TOP 20 {role_name} (RETRIEVAL ONLY) ---")
    for rank, idx in enumerate(top_indices):
        cand_id = all_cands[idx]['candidate_id']
        title = all_cands[idx].get('profile', {}).get('current_title', '')
        score = combined_score[idx]
        skills = " ".join([s.get('name', '') for s in (all_cands[idx].get('skills', []) or []) if isinstance(s, dict)][:5])
        out_lines.append(f"#{rank+1} | {title[:40].ljust(40)} | Score: {score:.3f} | Skills: {skills}")
    
    res = "\n".join(out_lines)
    print(res)
    with open(f"scratch/ablation_results.txt", "a", encoding="utf-8") as f:
        f.write(res + "\n")

if __name__ == "__main__":
    import os
    if os.path.exists("scratch/ablation_results.txt"):
        os.remove("scratch/ablation_results.txt")
    run_ablation("scratch/jd_frontend.txt", "Frontend Engineer")
    run_ablation("scratch/jd_sales.txt", "Sales Manager")
    run_ablation("scratch/jd_clinical.txt", "Clinical Research Scientist")
