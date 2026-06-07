import pandas as pd
import numpy as np
import lightgbm as lgb
import json
import os
import sys
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

def create_labels(df, w_ret, w_tech, w_prod, w_consist, w_hire):
    # Normalize components
    
    # 1. Retrieval
    retrieval_component = df['semantic_sim'] * 0.6 + df['bm25_score'] * 0.4
    
    # 2. Technical
    tech_component = (
        (df['retrieval_experience_score'].clip(0, 10) / 10.0) * 0.35 +
        (df['ranking_experience_score'].clip(0, 10) / 10.0) * 0.35 +
        (df['vector_db_score'].clip(0, 10) / 10.0) * 0.20 +
        (df['evaluation_framework_score'].clip(0, 10) / 10.0) * 0.10
    )
    
    # 3. Production
    prod_component = df['production_ml_score'].clip(0, 10) / 10.0
    
    # 4. Consistency
    consist_component = (
        df['career_consistency_score'].clip(0, 1) * 0.5 +
        ((df['timeline_consistency_score'].clip(-1, 1) + 1) / 2.0) * 0.5
    )
    
    # 5. Hireability
    hire_component = (
        (df['hireability_score'].clip(0, 10) / 10.0) * 0.5 +
        (df['startup_readiness_score'].clip(0, 10) / 10.0) * 0.2 +
        (df['leadership_score'].clip(0, 10) / 10.0) * 0.2 +
        (df['product_ownership_score'].clip(0, 10) / 10.0) * 0.1
    )
    
    raw_score = (
        retrieval_component * w_ret +
        tech_component * w_tech +
        prod_component * w_prod +
        consist_component * w_consist +
        hire_component * w_hire
    )
    
    # Convert continuous score to 1-4 buckets using quantiles
    q75 = np.percentile(raw_score, 75)
    q90 = np.percentile(raw_score, 90)
    q98 = np.percentile(raw_score, 98)
    
    labels = np.ones(len(raw_score), dtype=int)
    labels[raw_score >= q75] = 2
    labels[raw_score >= q90] = 3
    labels[raw_score >= q98] = 4
    
    return labels

def main():
    print("Loading JD and 10,000 candidates...")
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
        for i, line in enumerate(f):
            if i >= 10000: break
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
            except:
                pass
                
    print("Computing BM25...")
    bm25_scores = get_lexical_scores(jd_text, corpus_texts)
    # Scale bm25
    bm25_norm = np.clip(bm25_scores / (np.percentile(bm25_scores, 99) + 1e-9), 0, 1)
    
    print("Loading precomputed embeddings...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    emb_path = r"hackathon_pipeline/candidate_embeddings.npy"
    if not os.path.exists(emb_path):
        emb_path = r"candidate_embeddings.npy"
    doc_embs_full = np.load(emb_path)
    doc_embs = doc_embs_full[:10000].astype(np.float16)
    
    print("Encoding JD Chunks...")
    jd_words = jd_text.split()
    chunk_size = 200
    overlap = 50
    jd_chunks = []
    for i in range(0, max(1, len(jd_words) - overlap), chunk_size - overlap):
        chunk = " ".join(jd_words[i:i + chunk_size])
        if chunk: jd_chunks.append(chunk)
            
    chunk_embs = embedder.encode(jd_chunks, convert_to_numpy=True).astype(np.float16)
    
    print("Computing Top-5 Mean Semantic Similarities...")
    sim_matrix = doc_embs.dot(chunk_embs.T)
    sorted_sims = np.sort(sim_matrix, axis=1)[:, ::-1]
    semantic_sims = np.mean(sorted_sims[:, :5], axis=1)
    semantic_norm = np.clip(semantic_sims, 0, 1)
    
    df_cands = pd.DataFrame(cands_data)
    print("Extracting recruiter features...")
    feat_df = extract_recruiter_features(df_cands)
    feat_df['semantic_sim'] = semantic_norm
    feat_df['bm25_score'] = bm25_norm
    
    # Generate labels
    print("Generating Pseudo-Labels...")
    
    # Label A (Conservative)
    # 30 Retrieval, 30 Technical, 20 Production, 10 Consistency, 10 Hireability
    feat_df['label_A'] = create_labels(feat_df, 0.30, 0.30, 0.20, 0.10, 0.10)
    
    # Label B (Retrieval Heavy)
    # 45 Retrieval, 25 Technical, 15 Production, 10 Consistency, 5 Hireability
    feat_df['label_B'] = create_labels(feat_df, 0.45, 0.25, 0.15, 0.10, 0.05)
    
    # Label C (Balanced)
    # 35 Retrieval, 25 Technical, 20 Production, 10 Consistency, 10 Hireability
    feat_df['label_C'] = create_labels(feat_df, 0.35, 0.25, 0.20, 0.10, 0.10)
    
    def train_model(label_col, model_name):
        print(f"\nTraining {model_name} on {label_col}...")
        group = [len(feat_df)]
        train_data = lgb.Dataset(feat_df[FEATURE_COLS], label=feat_df[label_col], group=group)
        
        params = {
            'objective': 'lambdarank',
            'metric': 'ndcg',
            'ndcg_eval_at': [10, 20],
            'learning_rate': 0.05,
            'num_leaves': 31,
            'min_data_in_leaf': 20,
            'feature_fraction': 0.8,
            'verbose': -1,
            'seed': 42
        }
        
        bst = lgb.train(params, train_data, num_boost_round=100)
        bst.save_model(model_name)
        print(f"Saved {model_name}")

    train_model('label_A', 'lgbm_ranker_A.txt')
    train_model('label_B', 'lgbm_ranker_B.txt')
    train_model('label_C', 'lgbm_ranker_C.txt')

if __name__ == "__main__":
    main()
