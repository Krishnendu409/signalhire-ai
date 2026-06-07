import pandas as pd
import numpy as np
import json
import lightgbm as lgb
from sentence_transformers import SentenceTransformer
from scipy.stats import rankdata
from transformers import AutoTokenizer
import zipfile
import xml.etree.ElementTree as ET
import os

# ---------------------------------------------------------
# ONTOLOGY EXPANSION + LEXICAL DIVERGENCE
# ---------------------------------------------------------
def get_docx_text(path):
    z = zipfile.ZipFile(path)
    xml_content = z.read('word/document.xml')
    z.close()
    tree = ET.XML(xml_content)
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join(''.join(n.text for n in p.iter(w + 't') if n.text) for p in tree.iter(w + 'p') if any(n.text for n in p.iter(w + 't')))

import re
def _score_keywords_bounded(text_blocks, keywords):
    score = 0.0
    sorted_kw = sorted(keywords, key=len, reverse=True)
    for text, weight in text_blocks:
        if not text: continue
        t = text.lower()
        matched_spans = []
        for kw in sorted_kw:
            pattern = r'\b' + re.escape(kw.lower()) + r'\b'
            for m in re.finditer(pattern, t):
                start, end = m.start(), m.end()
                if not any(start < me and end > ms for ms, me in matched_spans):
                    score += weight
                    matched_spans.append((start, end))
    return min(score, 10.0)

def extract_features(df):
    features = pd.DataFrame(index=df.index)
    for idx, row in df.iterrows():
        profile = row.get('profile', {}) or {}
        headline = profile.get('headline', '') or ''
        summary = profile.get('summary', '') or ''
        current_title = profile.get('current_title', '') or ''
        
        career = row.get('career_history', []) or []
        current_job_text = ""
        past_jobs_text = ""
        if career:
            current_job_text = ((career[0].get('title', '') or '') + " " + (career[0].get('description', '') or '')).lower()
            if len(career) > 1:
                past_jobs_text = " ".join([((j.get('title', '') or '') + " " + (j.get('description', '') or '')) for j in career[1:]]).lower()
                
        skills_list = row.get('skills', []) or []
        skills_text = " ".join([s.get('name', '') for s in skills_list])
        
        text_blocks = [
            (headline + " " + summary, 1.5),
            (current_job_text, 2.0),
            (past_jobs_text, 0.8),
            (skills_text, 1.0)
        ]
        
        # Expanded Ontology
        features.at[idx, 'retrieval_experience_score'] = _score_keywords_bounded(text_blocks, [
            'retrieval', 'semantic search', 'information retrieval', 'search engine',
            'query understanding', 'document retrieval', 'dense retrieval',
            'sparse retrieval', 'hybrid retrieval', 'catalog search'
        ])
        features.at[idx, 'ranking_experience_score'] = _score_keywords_bounded(text_blocks, [
            'ranking', 'learning to rank', 'learning-to-rank', 'recommender',
            'lambdamart', 'xgboost ranker', 'search ranking', 'relevance engineering',
            'search infrastructure', 'product discovery', 'search quality'
        ])
        features.at[idx, 'vector_db_score'] = _score_keywords_bounded(text_blocks, [
            'pinecone', 'qdrant', 'milvus', 'weaviate', 'faiss', 'elasticsearch',
            'opensearch', 'vector database', 'chromadb', 'hnsw', 'ann',
            'approximate nearest neighbor', 'inverted index', 'lucene', 'vector index'
        ])
        features.at[idx, 'evaluation_framework_score'] = _score_keywords_bounded(text_blocks, [
            'ndcg', 'mrr', 'mean reciprocal rank', 'map', 'precision at k'
        ])
        features.at[idx, 'production_ml_score'] = _score_keywords_bounded(text_blocks, ['deployed', 'production', 'mlops', 'aws sagemaker', 'inference'])
        
        # Simplified Soft features
        signals = row.get('redrob_signals', {}) or {}
        features.at[idx, 'hireability_score'] = min(5.0, (signals.get('recruiter_response_rate', 0.0) * 3 + signals.get('interview_completion_rate', 0.5) * 2))
        features.at[idx, 'startup_readiness_score'] = _score_keywords_bounded(text_blocks, ['startup', 'early stage', 'wore many hats', '0 to 1'])
        features.at[idx, 'leadership_score'] = _score_keywords_bounded(text_blocks, ['led', 'managed', 'mentored', 'architected'])
        features.at[idx, 'career_consistency_score'] = 1.0 # simplified for test
        features.at[idx, 'candidate_id'] = row['candidate_id']
        features.at[idx, 'current_title'] = current_title
        
    return features

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("Loading JD...")
    jd_text = get_docx_text(r"C:\Users\krish\Documents\signalhire\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\job_description.docx")
    
    print("Loading candidates (10k sample)...")
    records = []
    corpus_texts = []
    with open(r"C:\Users\krish\Documents\signalhire\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl", 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 10000: break
            if line.strip():
                try:
                    cand = json.loads(line)
                    records.append(cand)
                    profile = cand.get('profile', {}) or {}
                    corpus_texts.append(profile.get('headline', '') + " " + profile.get('summary', ''))
                except: continue
                
    df = pd.DataFrame(records)
    features_df = extract_features(df)
    
    # ---------------------------------------------------------
    # JD CHUNKING SEMANTIC SEARCH
    # ---------------------------------------------------------
    print("Embedding JD chunks and candidates...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    
    tokens = tokenizer.encode(jd_text, add_special_tokens=False)
    chunk_size = 500
    jd_chunks = [tokenizer.decode(tokens[i:i+chunk_size]) for i in range(0, len(tokens), chunk_size)]
    
    query_embs = embedder.encode(jd_chunks, convert_to_numpy=True)
    doc_embs = embedder.encode(corpus_texts, convert_to_numpy=True)
    
    sim_matrix = doc_embs.dot(query_embs.T)
    max_sims = sim_matrix.max(axis=1)
    features_df['semantic_sim'] = max_sims
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus_texts + [jd_text])
    bm25_all = tfidf_matrix[:-1].dot(tfidf_matrix[-1].T).toarray().flatten()
    features_df['bm25_score'] = bm25_all
    
    # Lexical-Semantic Divergence
    from scipy.stats import rankdata
    bm25_pct = rankdata(bm25_all) / len(bm25_all)
    sem_pct = rankdata(max_sims) / len(max_sims)
    features_df['lexical_semantic_divergence'] = bm25_pct - sem_pct
    
    # RRF
    features_df['rrf_score'] = (1.0 / (60 + (len(bm25_all) - rankdata(bm25_all) + 1))) + (1.0 / (60 + (len(max_sims) - rankdata(max_sims) + 1)))

    # ---------------------------------------------------------
    # NEW PSEUDO-LABEL (Balanced Composite)
    # ---------------------------------------------------------
    # Retrieval + Production + Consistency + Hireability + Leadership + Rare Expert Signals
    norm_sim = (max_sims - max_sims.min()) / (max_sims.max() - max_sims.min() + 1e-9)
    norm_bm25 = (bm25_all - bm25_all.min()) / (bm25_all.max() - bm25_all.min() + 1e-9)
    
    composite = (
        (norm_sim * 2.0 + norm_bm25 * 1.0) +  # Retrieval
        features_df['production_ml_score'] * 0.5 + 
        features_df['hireability_score'] * 0.5 +
        features_df['leadership_score'] * 0.3 +
        features_df['evaluation_framework_score'] * 1.5 + # Rare Expert
        features_df['ranking_experience_score'] * 1.0 +
        features_df['vector_db_score'] * 0.5
    )
    
    p95, p80, p50 = np.percentile(composite, [95, 80, 50])
    labels = np.zeros(len(composite))
    labels[composite >= p95] = 3
    labels[(composite < p95) & (composite >= p80)] = 2
    labels[(composite < p80) & (composite >= p50)] = 1
    features_df['label'] = labels

    # ---------------------------------------------------------
    # TRAIN MODEL A (with RRF)
    # ---------------------------------------------------------
    model_a_cols = [
        'semantic_sim', 'bm25_score', 'rrf_score', 'lexical_semantic_divergence',
        'retrieval_experience_score', 'ranking_experience_score', 'vector_db_score',
        'evaluation_framework_score', 'production_ml_score', 'hireability_score',
        'startup_readiness_score', 'leadership_score'
    ]
    train_data_a = lgb.Dataset(features_df[model_a_cols], label=labels, group=[len(labels)])
    params = {'objective': 'lambdarank', 'verbosity': -1, 'min_data_in_leaf': 10}
    model_a = lgb.train(params, train_data_a, num_boost_round=100)
    scores_a = model_a.predict(features_df[model_a_cols])
    
    # Linear Residual
    features_df['score_a'] = scores_a + (features_df['evaluation_framework_score'] * 1.5)

    # ---------------------------------------------------------
    # TRAIN MODEL B (without RRF)
    # ---------------------------------------------------------
    model_b_cols = [c for c in model_a_cols if c != 'rrf_score']
    train_data_b = lgb.Dataset(features_df[model_b_cols], label=labels, group=[len(labels)])
    model_b = lgb.train(params, train_data_b, num_boost_round=100)
    scores_b = model_b.predict(features_df[model_b_cols])
    features_df['score_b'] = scores_b + (features_df['evaluation_framework_score'] * 1.5)

    # ---------------------------------------------------------
    # ABLATION RESULTS
    # ---------------------------------------------------------
    top20_a = set(features_df.sort_values('score_a', ascending=False).head(20)['candidate_id'])
    top20_b = set(features_df.sort_values('score_b', ascending=False).head(20)['candidate_id'])
    overlap_20 = len(top20_a & top20_b)
    
    top100_a = set(features_df.sort_values('score_a', ascending=False).head(100)['candidate_id'])
    top100_b = set(features_df.sort_values('score_b', ascending=False).head(100)['candidate_id'])
    overlap_100 = len(top100_a & top100_b)

    print(f"\nRRF Ablation Results:")
    print(f"Top 20 Overlap: {overlap_20}/20")
    print(f"Top 100 Overlap: {overlap_100}/100")
    print("\nFeature Importance (Model A w/ RRF):")
    for name, imp in sorted(zip(model_a_cols, model_a.feature_importance('gain')), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {name}: {imp:.2f}")
        
    print("\nFeature Importance (Model B w/o RRF):")
    for name, imp in sorted(zip(model_b_cols, model_b.feature_importance('gain')), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {name}: {imp:.2f}")

    # ---------------------------------------------------------
    # TOP 20 SHIFT REPORT
    # ---------------------------------------------------------
    print("\n=========================================")
    print("CURRENT VS PROPOSED TOP 20 (Sample of 10k)")
    print("=========================================\n")
    
    # Since we don't have the original model scores for this exact 10k subset easily mapped,
    # we'll run the old heuristic to get "Current" Top 20 vs Model B's Top 20
    old_core = (features_df['ranking_experience_score'] * 3.0 + features_df['vector_db_score'] * 1.5)
    features_df['score_old'] = old_core + (features_df['rrf_score'] * 50)
    
    top_old = features_df.sort_values('score_old', ascending=False).head(20)
    top_new = features_df.sort_values('score_b', ascending=False).head(20)
    
    new_ids = top_new['candidate_id'].tolist()
    old_ids = top_old['candidate_id'].tolist()
    
    for rank, cid in enumerate(new_ids, 1):
        row = features_df[features_df['candidate_id'] == cid].iloc[0]
        status = "PROMOTED" if cid not in old_ids else "STABLE"
        print(f"Rank {rank} | {cid} | {status} | Role: {row['current_title']}")
        if status == "PROMOTED":
            print(f"  -> Why: High new ontology ({row['vector_db_score']}) / Eval Score ({row['evaluation_framework_score']}) / LexDvrg ({row['lexical_semantic_divergence']:.2f})")
            
    print("\n--- DEMOTED FROM TOP 20 ---")
    for cid in old_ids:
        if cid not in new_ids:
            row = features_df[features_df['candidate_id'] == cid].iloc[0]
            new_rank = features_df.sort_values('score_b', ascending=False).reset_index().index[features_df.sort_values('score_b', ascending=False)['candidate_id'] == cid].tolist()[0] + 1
            print(f"{cid} | Dropped to Rank {new_rank} | Role: {row['current_title']}")
            print(f"  -> Why: Low hireability ({row['hireability_score']}) or keyword stuffed (Divergence: {row['lexical_semantic_divergence']:.2f})")

if __name__ == "__main__":
    main()
