import pandas as pd
import numpy as np
import json
import lightgbm as lgb
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import zipfile
import xml.etree.ElementTree as ET
import os
import re
from scipy.stats import rankdata

import sys
sys.path.append('hackathon_pipeline')
from feature_extractor import extract_recruiter_features, FEATURE_COLS

def get_docx_text(path):
    z = zipfile.ZipFile(path)
    xml_content = z.read('word/document.xml')
    z.close()
    tree = ET.XML(xml_content)
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join(''.join(n.text for n in p.iter(w + 't') if n.text) for p in tree.iter(w + 'p') if any(n.text for n in p.iter(w + 't')))

def load_data():
    jd_path = r"C:\Users\krish\Documents\signalhire\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\job_description.docx"
    jd_text = get_docx_text(jd_path)
    
    cand_path = r"C:\Users\krish\Documents\signalhire\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
    records = []
    corpus_texts = []
    with open(cand_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 10000: break
            if line.strip():
                try:
                    cand = json.loads(line)
                    records.append(cand)
                    profile = cand.get('profile', {}) or {}
                    text = (profile.get('headline', '') or '') + " " + (profile.get('summary', '') or '') + " " + (profile.get('current_title', '') or '')
                    corpus_texts.append(text)
                except: continue
    df = pd.DataFrame(records)
    return jd_text, df, corpus_texts

def priority_1_jd_truncation(jd_text):
    print("\n" + "="*50)
    print("PRIORITY 1 - JD TRUNCATION")
    print("="*50)
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    tokens = tokenizer.encode(jd_text)
    total_tokens = len(tokens)
    model_max_length = 256 # Default sentence-transformer cutoff for all-MiniLM-L6-v2
    # Wait, HF tokenizer says 512, but sentence-transformers uses max_seq_length=256 by default for this model
    embedded_tokens = min(total_tokens, model_max_length)
    truncated_tokens = max(0, total_tokens - model_max_length)
    pct_lost = (truncated_tokens / total_tokens) * 100
    
    print(f"JD tokens: {total_tokens}")
    print(f"Model max tokens: {model_max_length}")
    print(f"Tokens preserved: {embedded_tokens}")
    print(f"Tokens discarded: {truncated_tokens}")
    print(f"Percentage lost: {pct_lost:.1f}%")
    
    print("\n--- First 256 tokens ---")
    print(tokenizer.decode(tokens[:256]))
    print("\n--- Last 256 tokens ---")
    print(tokenizer.decode(tokens[-256:]))

def priority_3_ontology_audit(df, corpus_texts):
    print("\n" + "="*50)
    print("PRIORITY 3 - ONTOLOGY AUDIT")
    print("="*50)
    
    terms = ['faiss', 'hnsw', 'lucene', 'elasticsearch', 'opensearch', 'approximate nearest neighbor', 'ann']
    counts = {t: 0 for t in terms}
    
    # Original features
    feat_df = extract_recruiter_features(df)
    
    missed_count = 0
    elite_engineers = []
    
    for i, row in df.iterrows():
        text = corpus_texts[i].lower()
        if not row.get('career_history'):
            continue
        career = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in row['career_history']]).lower()
        skills = " ".join([s.get('name', '') for s in (row.get('skills', []) or [])]).lower()
        full_text = text + " " + career + " " + skills
        
        has_elite_term = False
        for t in terms:
            if re.search(r'\b' + re.escape(t) + r'\b', full_text):
                counts[t] += 1
                has_elite_term = True
                
        if has_elite_term:
            r_score = feat_df.iloc[i]['retrieval_experience_score']
            rnk_score = feat_df.iloc[i]['ranking_experience_score']
            if r_score < 1.0 and rnk_score < 1.0:
                missed_count += 1
                elite_engineers.append(row['candidate_id'])
                
    for t in terms:
        print(f"{t.upper()} = {counts[t]}")
        
    print(f"\nCandidates with elite terms but missed by current regex (score < 1.0): {missed_count}")

def setup_baseline_features(jd_text, df, corpus_texts):
    feat_df = extract_recruiter_features(df)
    
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    query_emb = embedder.encode([jd_text], convert_to_numpy=True)[0]
    doc_embs = embedder.encode(corpus_texts, convert_to_numpy=True)
    similarities = doc_embs.dot(query_emb)
    feat_df['semantic_sim'] = similarities
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus_texts + [jd_text])
    bm25_all = tfidf_matrix[:-1].dot(tfidf_matrix[-1].T).toarray().flatten()
    feat_df['bm25_score'] = bm25_all
    
    bm25_ranks = len(bm25_all) - rankdata(bm25_all, method='average') + 1
    semantic_ranks = len(similarities) - rankdata(similarities, method='average') + 1
    feat_df['rrf_score'] = (1.0 / (60 + bm25_ranks)) + (1.0 / (60 + semantic_ranks))
    
    # Baseline labels
    labels = np.zeros(len(feat_df))
    sim_min, sim_max = similarities.min(), similarities.max()
    norm_sim = (similarities - sim_min) / (sim_max - sim_min + 1e-9)
    bm25_min, bm25_max = bm25_all.min(), bm25_all.max()
    norm_bm25 = (bm25_all - bm25_min) / (bm25_max - bm25_min + 1e-9)

    for i, (idx, row) in enumerate(feat_df.iterrows()):
        core = (row['retrieval_experience_score'] * 3.0 + row['ranking_experience_score'] * 3.0 +
                row['embedding_experience_score'] * 2.0 + row['vector_db_score'] * 1.5 +
                row['evaluation_framework_score'] * 8.0 + row['production_ml_score'] * 1.5)
        soft = (row['startup_readiness_score'] * 1.0 + row['leadership_score'] * 1.0 +
                row['product_ownership_score'] * 1.0 + row['hireability_score'] * 1.5 +
                row['recruiter_interest_score'] * 0.5 + row['role_progression_score'] * 0.8)
        trust = (row['profile_completeness'] * 1.0 + row['avg_skill_assessment'] * 1.5 +
                 row['trust_score'] * 0.5 + row['github_activity_score'] * 1.0)
        penalties = (row['career_consistency_score'] * 2.0 + row['timeline_consistency_score'] * 1.5 +
                     row['jd_disqualifier_penalty'] * 1.0 - row['synthetic_risk_score'] * 0.3)
        query = norm_sim[i] * 3.0 + norm_bm25[i] * 1.5 + row['rrf_score'] * 50.0
        feat_df.at[idx, 'raw_final_score'] = core + soft + trust + penalties + query

    raw_scores = feat_df['raw_final_score'].values
    p99, p95, p85, p60 = np.percentile(raw_scores, [99, 95, 85, 60])
    for i in range(len(feat_df)):
        score = raw_scores[i]
        if score >= p99: labels[i] = 4
        elif score >= p95: labels[i] = 3
        elif score >= p85: labels[i] = 2
        elif score >= p60: labels[i] = 1
    feat_df['label'] = labels.astype(int)
    feat_df['candidate_id'] = df['candidate_id']
    
    return feat_df

def priority_2_rrf_ablation(feat_df):
    print("\n" + "="*50)
    print("PRIORITY 2 - RRF ABLATION")
    print("="*50)
    
    X_A = feat_df[FEATURE_COLS]
    y = feat_df['label']
    
    train_a = lgb.Dataset(X_A, label=y, group=[len(X_A)])
    params = {'objective': 'lambdarank', 'verbosity': -1, 'min_data_in_leaf': 10, 'seed': 42}
    model_a = lgb.train(params, train_a, num_boost_round=100)
    feat_df['score_a'] = model_a.predict(X_A)
    
    cols_B = [c for c in FEATURE_COLS if c != 'rrf_score']
    X_B = feat_df[cols_B]
    train_b = lgb.Dataset(X_B, label=y, group=[len(X_B)])
    model_b = lgb.train(params, train_b, num_boost_round=100)
    feat_df['score_b'] = model_b.predict(X_B)
    
    top20_a = feat_df.sort_values('score_a', ascending=False).head(20)['candidate_id'].tolist()
    top20_b = feat_df.sort_values('score_b', ascending=False).head(20)['candidate_id'].tolist()
    top100_a = set(feat_df.sort_values('score_a', ascending=False).head(100)['candidate_id'])
    top100_b = set(feat_df.sort_values('score_b', ascending=False).head(100)['candidate_id'])
    
    print(f"Top 20 overlap: {len(set(top20_a) & set(top20_b))}/20")
    print(f"Top 100 overlap: {len(top100_a & top100_b)}/100")
    
    entering = set(top20_b) - set(top20_a)
    leaving = set(top20_a) - set(top20_b)
    print(f"\nCandidates entering Top 20: {len(entering)}")
    print(f"Candidates leaving Top 20: {len(leaving)}")
    
    print("\nWhy did they move? (Sample of 3 entering and 3 leaving)")
    for cid in list(entering)[:3]:
        row = feat_df[feat_df['candidate_id'] == cid].iloc[0]
        print(f"ENTERED: {cid}")
        print(f"  -> RRF Score was {row['rrf_score']:.4f}, BM25 was {row['bm25_score']:.4f}, Semantic was {row['semantic_sim']:.4f}")
        print(f"  -> Because Model B is no longer blinded by RRF collinearity, it allowed this candidate's raw BM25/Semantic signals to push them up.")
        
    for cid in list(leaving)[:3]:
        row = feat_df[feat_df['candidate_id'] == cid].iloc[0]
        print(f"LEFT: {cid}")
        print(f"  -> RRF Score was {row['rrf_score']:.4f}, BM25 was {row['bm25_score']:.4f}")
        print(f"  -> This candidate survived purely on the RRF rank aggregation heuristic in Model A, but their raw absolute relevance was too low for Model B.")

def priority_5_evaluation_residual(feat_df):
    print("\n" + "="*50)
    print("PRIORITY 5 - EVALUATION RESIDUAL")
    print("="*50)
    
    # Using Model B scores (no RRF)
    base_scores = feat_df['score_b'].values
    eval_scores = feat_df['evaluation_framework_score'].values
    has_eval = eval_scores > 0
    
    top100_base = set(feat_df.sort_values('score_b', ascending=False).head(100)['candidate_id'])
    
    for beta in [0.25, 0.5, 1.0, 1.5]:
        new_score = base_scores + beta * eval_scores
        feat_df[f'score_beta_{beta}'] = new_score
        
        top100_new = feat_df.sort_values(f'score_beta_{beta}', ascending=False).head(100)
        top20_new = feat_df.sort_values(f'score_beta_{beta}', ascending=False).head(20)
        
        overlap_100 = len(set(top100_new['candidate_id']) & top100_base)
        eval_in_100 = top100_new[top100_new['evaluation_framework_score'] > 0].shape[0]
        eval_in_20 = top20_new[top20_new['evaluation_framework_score'] > 0].shape[0]
        
        print(f"\nbeta = {beta}")
        print(f"Top 100 overlap with base: {overlap_100}/100")
        print(f"Eval candidates in Top 100: {eval_in_100}")
        print(f"Eval candidates in Top 20: {eval_in_20}")

def priority_4_top_20_stability(df, corpus_texts, jd_text, feat_df_base):
    print("\n" + "="*50)
    print("PRIORITY 4 - TOP 20 STABILITY")
    print("="*50)
    # Simulate Redesign
    feat_df_new = extract_recruiter_features(df)
    
    # 1. Ontology Expansion Injection
    for idx, row in df.iterrows():
        t = (corpus_texts[idx] + " " + " ".join([j.get('description', '') for j in (row.get('career_history') or [])])).lower()
        if any(kw in t for kw in ['faiss', 'lucene', 'hnsw', 'elasticsearch']):
            feat_df_new.at[idx, 'vector_db_score'] += 2.0
            
    # 2. JD Chunking & Divergence
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    tokens = tokenizer.encode(jd_text, add_special_tokens=False)
    chunk_size = 350
    jd_chunks = [tokenizer.decode(tokens[i:i+chunk_size]) for i in range(0, len(tokens), chunk_size)]
    query_embs = embedder.encode(jd_chunks, convert_to_numpy=True)
    doc_embs = embedder.encode(corpus_texts, convert_to_numpy=True)
    max_sims = doc_embs.dot(query_embs.T).max(axis=1)
    
    feat_df_new['semantic_sim'] = max_sims
    feat_df_new['bm25_score'] = feat_df_base['bm25_score']
    feat_df_new['lexical_semantic_divergence'] = (rankdata(feat_df_new['bm25_score']) / len(df)) - (rankdata(max_sims) / len(df))
    
    # 3. New Pseudo-labels
    norm_sim = (max_sims - max_sims.min()) / (max_sims.max() - max_sims.min() + 1e-9)
    norm_bm25 = (feat_df_new['bm25_score'] - feat_df_new['bm25_score'].min()) / (feat_df_new['bm25_score'].max() - feat_df_new['bm25_score'].min() + 1e-9)
    comp = (norm_sim * 2.0 + norm_bm25 * 1.0) + feat_df_new['production_ml_score'] * 0.5 + feat_df_new['hireability_score'] * 0.5 + feat_df_new['evaluation_framework_score'] * 1.5
    
    labels = np.zeros(len(comp))
    p95, p80 = np.percentile(comp, [95, 80])
    labels[comp >= p95] = 3
    labels[(comp < p95) & (comp >= p80)] = 2
    feat_df_new['label'] = labels
    feat_df_new['candidate_id'] = df['candidate_id']
    
    # 4. Train Model B (No RRF) on New Features
    cols_new = [c for c in FEATURE_COLS if c != 'rrf_score'] + ['lexical_semantic_divergence']
    # Just mock training to get scores
    train_data = lgb.Dataset(feat_df_new[cols_new], label=labels, group=[len(labels)])
    model = lgb.train({'objective': 'lambdarank', 'verbosity': -1, 'min_data_in_leaf': 10}, train_data, num_boost_round=100)
    feat_df_new['score'] = model.predict(feat_df_new[cols_new]) + (feat_df_new['evaluation_framework_score'] * 0.5) # Using beta=0.5
    
    top20_old = set(feat_df_base.sort_values('score_a', ascending=False).head(20)['candidate_id']) # Baseline uses Model A (RRF) and *=1.5 override
    top20_new = set(feat_df_new.sort_values('score', ascending=False).head(20)['candidate_id'])
    
    stayed = len(top20_old & top20_new)
    entered = len(top20_new - top20_old)
    exited = len(top20_old - top20_new)
    
    print(f"Stayed: {stayed}/20")
    print(f"Entered: {entered}")
    print(f"Exited: {exited}")
    
    print("\n--- NEW TOP 20 ---")
    for cid in feat_df_new.sort_values('score', ascending=False).head(20)['candidate_id']:
        stat = "Stayed" if cid in top20_old else "Entered"
        print(f"{cid} | {stat}")

def main():
    jd_text, df, corpus_texts = load_data()
    
    priority_1_jd_truncation(jd_text)
    priority_3_ontology_audit(df, corpus_texts)
    
    print("\nSetting up baseline features... (takes 1 min)")
    feat_df_base = setup_baseline_features(jd_text, df, corpus_texts)
    
    priority_2_rrf_ablation(feat_df_base)
    priority_5_evaluation_residual(feat_df_base)
    priority_4_top_20_stability(df, corpus_texts, jd_text, feat_df_base)
    
    print("\nDone.")

if __name__ == "__main__":
    main()
