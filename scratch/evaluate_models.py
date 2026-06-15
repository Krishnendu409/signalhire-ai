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

def get_category(title, career_text):
    t = title.lower()
    c = career_text.lower()
    if 'search' in t or 'search' in c or 'retrieval' in t or 'retrieval' in c: return 'Search Engineer'
    elif 'nlp' in t or 'nlp' in c or 'natural language' in t or 'natural language' in c: return 'NLP Engineer'
    elif 'recommend' in t or 'recommend' in c or 'ranking' in t or 'ranking' in c: return 'Recommendation Engineer'
    elif 'machine learning' in t or 'ml' in t or 'machine learning' in c or 'ml ' in c: return 'Applied ML Engineer'
    elif 'software' in t or 'developer' in t or 'backend' in t: return 'Software Engineer'
    else: return 'Other'

def get_interviewability(df_cands, top_n=20):
    yes_c = 0; maybe_c = 0; no_c = 0
    for i in range(top_n):
        c = df_cands.iloc[i]
        p = c.get('profile', {}) or {}
        title = p.get('current_title', '') or ''
        yrs = p.get('years_of_experience', 0)
        t_lower = title.lower()
        if yrs >= 4 and any(x in t_lower for x in ['search', 'nlp', 'ml', 'ai', 'data scientist', 'machine learning', 'retrieval', 'ranking']):
            yes_c += 1
        elif yrs >= 2 and any(x in t_lower for x in ['search', 'nlp', 'ml', 'ai', 'data scientist', 'machine learning', 'retrieval', 'ranking', 'engineer', 'developer', 'software']):
            maybe_c += 1
        else:
            no_c += 1
    return yes_c, maybe_c, no_c

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
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    emb_path = r"hackathon_pipeline/candidate_embeddings.npy"
    if not os.path.exists(emb_path):
        emb_path = r"candidate_embeddings.npy"
    doc_embs = np.load(emb_path).astype(np.float16)
    
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
    
    models = {
        'Current': 'lgbm_ranker.txt',
        'Model A (Conservative)': 'lgbm_ranker_A.txt',
        'Model B (Retrieval Heavy)': 'lgbm_ranker_B.txt',
        'Model C (Balanced)': 'lgbm_ranker_C.txt'
    }
    
    results = {}
    
    for name, path in models.items():
        if not os.path.exists(path): continue
        model = lgb.Booster(model_file=path)
        scores = model.predict(features_df[FEATURE_COLS])
        
        top20_idx = np.argsort(scores)[::-1][:20]
        top100_idx = np.argsort(scores)[::-1][:100]
        
        df_top20 = df_union.iloc[top20_idx]
        df_top100 = df_union.iloc[top100_idx]
        
        # Interviewability
        yes, maybe, no = get_interviewability(df_top20)
        
        # Category Distribution
        cats = {'Search Engineer':0, 'NLP Engineer':0, 'Applied ML Engineer':0, 'Recommendation Engineer':0, 'Software Engineer':0, 'Other':0}
        for i in range(100):
            c = df_top100.iloc[i]
            title = c.get('profile', {}).get('current_title', '')
            career = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in (c.get('career_history', []) or [])])
            cats[get_category(title, career)] += 1
            
        # Search Specialist Penetration @ 20
        spec_count = 0
        specialist_terms = ['faiss', 'qdrant', 'lucene', 'opensearch', 'learning-to-rank', 'learning to rank', 'retrieval', 'ranking systems', 'vector database']
        for i in range(20):
            c = df_top20.iloc[i]
            title = c.get('profile', {}).get('current_title', '')
            career = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in (c.get('career_history', []) or [])]).lower()
            skills = " ".join([s.get('name', '') for s in (c.get('skills', []) or [])]).lower()
            text = f"{title.lower()} {career} {skills}"
            if any(t in text for t in specialist_terms):
                spec_count += 1
                
        # Retrieval-Relevance @ 20 (retrieval_score > 3.0 and ranking_score > 3.0)
        rr_count = 0
        f_top20 = features_df.iloc[top20_idx]
        for i in range(20):
            f = f_top20.iloc[i]
            if f['retrieval_experience_score'] >= 2.0 and f['ranking_experience_score'] >= 2.0:
                rr_count += 1
                
        results[name] = {
            'interviewability': (yes, maybe, no),
            'cats': cats,
            'specialists_20': spec_count,
            'rr_20': rr_count,
            'top20_cands': [c['candidate_id'] for _, c in df_top20.iterrows()]
        }
        
    print("\n" + "="*50)
    print("MODEL COMPARISON")
    print("="*50)
    for name, res in results.items():
        print(f"\n### {name}")
        print(f"Top 20 Interviewability -> YES: {res['interviewability'][0]}, MAYBE: {res['interviewability'][1]}, NO: {res['interviewability'][2]}")
        print(f"Top 20 Specialist Penetration -> {res['specialists_20']} / 20")
        print(f"Top 20 Retrieval-Relevance -> {res['rr_20']} / 20")
        print(f"Top 100 Category Distribution:")
        for k, v in res['cats'].items():
            if v > 0: print(f"  {k}: {v}")
            
    print("\n" + "="*50)
    print("NEWLY PROMOTED CANDIDATES (vs Current Model)")
    print("="*50)
    
    current_cands = set(results['Current']['top20_cands'])
    for name, res in results.items():
        if name == 'Current': continue
        new_cands = set(res['top20_cands']) - current_cands
        print(f"\n### Promoted into Top 20 by {name}:")
        if not new_cands:
            print("  None")
        for cid in list(new_cands)[:5]:
            c = next(c for _, c in df_union.iterrows() if c['candidate_id'] == cid)
            title = c.get('profile', {}).get('current_title', '')
            print(f"  - {cid} | {title}")

if __name__ == "__main__":
    main()
