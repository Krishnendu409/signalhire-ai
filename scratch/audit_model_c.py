import pandas as pd
import numpy as np
import lightgbm as lgb
import json
import sys
import os
from sentence_transformers import SentenceTransformer
import zipfile
import xml.etree.ElementTree as ET

sys.path.append('hackathon_pipeline')
from feature_extractor import extract_recruiter_features, get_lexical_scores, FEATURE_COLS

def get_docx_text(path):
    z = zipfile.ZipFile(path)
    xml_content = z.read('word/document.xml')
    z.close()
    tree = ET.XML(xml_content)
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join(''.join(n.text for n in p.iter(w + 't') if n.text) for p in tree.iter(w + 'p') if any(n.text for n in p.iter(w + 't')))

def is_interviewable(c):
    p = c.get('profile', {}) or {}
    title = p.get('current_title', '') or ''
    yrs = p.get('years_of_experience', 0)
    t_lower = title.lower()
    if yrs >= 4 and any(x in t_lower for x in ['search', 'nlp', 'ml', 'ai', 'data scientist', 'machine learning', 'retrieval', 'ranking']):
        return "YES"
    elif yrs >= 2 and any(x in t_lower for x in ['search', 'nlp', 'ml', 'ai', 'data scientist', 'machine learning', 'retrieval', 'ranking', 'engineer', 'developer', 'software']):
        return "MAYBE"
    else:
        return "NO"

def main():
    print("Loading JD and all candidates...")
    cands_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(cands_path):
        cands_path = r"../" + cands_path
        
    jd_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx"
    if not os.path.exists(jd_path):
        jd_path = r"../" + jd_path
        
    jd_text = get_docx_text(jd_path)
    
    cands_data = []
    corpus_texts = []
    with open(cands_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                c = json.loads(line)
                cands_data.append(c)
                p = c.get('profile', {}) or {}
                headline = p.get('headline', '') or ''
                summary = p.get('summary', '') or ''
                title = p.get('current_title', '') or ''
                skills = " ".join([s.get('name', '') for s in (c.get('skills', []) or [])])
                career = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in (c.get('career_history', []) or [])])
                
                full_text = f"{headline} {summary} {title} {skills} {career}"
                corpus_texts.append(full_text.lower())
            except: pass

    # Fast BM25 + Semantic
    print("Retrieving candidates...")
    bm25_scores = get_lexical_scores(jd_text, corpus_texts)
    
    print("Loading precomputed embeddings...")
    emb_path = r"hackathon_pipeline/candidate_embeddings.npy"
    if not os.path.exists(emb_path):
        emb_path = r"candidate_embeddings.npy"
    doc_embs = np.load(emb_path).astype(np.float16)
    
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    jd_words = jd_text.split()
    chunk_size = 200; overlap = 50
    jd_chunks = [" ".join(jd_words[i:i + chunk_size]) for i in range(0, max(1, len(jd_words) - overlap), chunk_size - overlap) if " ".join(jd_words[i:i + chunk_size])]
    chunk_embs = embedder.encode(jd_chunks, convert_to_numpy=True).astype(np.float16)
    
    sim_matrix = doc_embs.dot(chunk_embs.T)
    sorted_sims = np.sort(sim_matrix, axis=1)[:, ::-1]
    semantic_sims = np.mean(sorted_sims[:, :5], axis=1)
    
    top_k = 5000
    top_bm25_indices = set(np.argsort(bm25_scores)[::-1][:top_k])
    top_semantic_indices = set(np.argsort(semantic_sims)[::-1][:top_k])
    union_indices = list(top_bm25_indices | top_semantic_indices)
    
    print(f"Extracted {len(union_indices)} candidates. Computing features...")
    df_union = pd.DataFrame([cands_data[i] for i in union_indices])
    features_df = extract_recruiter_features(df_union)
    features_df['semantic_sim'] = np.clip(semantic_sims[union_indices], 0, 1)
    features_df['bm25_score'] = np.clip(bm25_scores[union_indices] / (np.percentile(bm25_scores, 99) + 1e-9), 0, 1)
    
    model = lgb.Booster(model_file="lgbm_ranker_C.txt")
    scores = model.predict(features_df[FEATURE_COLS])
    
    top20_idx = np.argsort(scores)[::-1][:20]
    
    print("\n==================================================")
    print("CHECK 1: THE SINGLE 'NO' CANDIDATE")
    print("==================================================")
    for i in range(20):
        idx = top20_idx[i]
        c = cands_data[union_indices[idx]]
        f = features_df.iloc[idx]
        status = is_interviewable(c)
        if status == "NO":
            title = c.get('profile', {}).get('current_title', '')
            yrs = c.get('profile', {}).get('years_of_experience', 0)
            print(f"Candidate ID: {c['candidate_id']}")
            print(f"Current Title: {title}")
            print(f"Years Experience: {yrs}")
            print(f"Retrieval Score: {f['semantic_sim']:.2f} (semantic), {f['bm25_score']:.2f} (bm25), {f['retrieval_experience_score']:.2f} (tech)")
            print(f"Ranking Score: {f['ranking_experience_score']:.2f}")
            print(f"Production ML Score: {f['production_ml_score']:.2f}")
            print(f"Hireability Score: {f['hireability_score']:.2f}")
            break

    print("\n==================================================")
    print("CHECK 2: TOP-10 RETRIEVAL EVIDENCE")
    print("==================================================")
    specialist_terms = ['faiss', 'qdrant', 'lucene', 'opensearch', 'elasticsearch', 'learning-to-rank', 'learning to rank', 'semantic search', 'hybrid retrieval']
    
    for i in range(10):
        idx = top20_idx[i]
        c = cands_data[union_indices[idx]]
        title = c.get('profile', {}).get('current_title', '')
        career = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in (c.get('career_history', []) or [])]).lower()
        skills = " ".join([s.get('name', '') for s in (c.get('skills', []) or [])]).lower()
        text = f"{title.lower()} {career} {skills}"
        
        found = [t for t in specialist_terms if t in text]
        print(f"[{i+1}] {c['candidate_id']} - {title}")
        print(f"    Evidence found: {found if found else 'NONE (semantic only)'}")

if __name__ == "__main__":
    main()
