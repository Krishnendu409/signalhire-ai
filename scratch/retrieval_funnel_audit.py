import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import zipfile
import xml.etree.ElementTree as ET
import sys
import os

sys.path.append('hackathon_pipeline')
from feature_extractor import extract_recruiter_features

def get_docx_text(path):
    z = zipfile.ZipFile(path)
    xml_content = z.read('word/document.xml')
    z.close()
    tree = ET.XML(xml_content)
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join(''.join(n.text for n in p.iter(w + 't') if n.text) for p in tree.iter(w + 'p') if any(n.text for n in p.iter(w + 't')))

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
                corpus_texts.append(full_text)
            except:
                pass
                
    print("Encoding Candidates...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    doc_embs = embedder.encode(corpus_texts, convert_to_numpy=True).astype(np.float16)
    
    print("Encoding JD Chunks...")
    jd_words = jd_text.split()
    chunk_size = 200
    overlap = 50
    jd_chunks = []
    for i in range(0, max(1, len(jd_words) - overlap), chunk_size - overlap):
        chunk = " ".join(jd_words[i:i + chunk_size])
        if chunk:
            jd_chunks.append(chunk)
            
    chunk_embs = embedder.encode(jd_chunks, convert_to_numpy=True).astype(np.float16)
    
    print("Computing Similarities...")
    sim_matrix = doc_embs.dot(chunk_embs.T)
    max_sims = np.max(sim_matrix, axis=1)
    
    sorted_sims = np.sort(sim_matrix, axis=1)[:, ::-1]
    top5_mean_sims = np.mean(sorted_sims[:, :5], axis=1)
    
    # We take top 500 out of 10,000 (which is 5%)
    # This simulates taking top 5000 out of 100,000
    top_k = 500
    maxsim_indices = np.argsort(max_sims)[::-1][:top_k]
    top5mean_indices = np.argsort(top5_mean_sims)[::-1][:top_k]
    
    maxsim_cands = [cands_data[i] for i in maxsim_indices]
    top5mean_cands = [cands_data[i] for i in top5mean_indices]
    
    df_maxsim = pd.DataFrame(maxsim_cands)
    df_top5mean = pd.DataFrame(top5mean_cands)
    
    print("Extracting features for MaxSim Top 500...")
    feat_maxsim = extract_recruiter_features(df_maxsim)
    
    print("Extracting features for Top-5 Mean Top 500...")
    feat_top5mean = extract_recruiter_features(df_top5mean)
    
    print("\n" + "="*50)
    print("RETRIEVAL POPULATION AUDIT (TOP 5%)")
    print("="*50)
    
    metrics = [
        'retrieval_experience_score',
        'ranking_experience_score',
        'production_ml_score',
        'hireability_score'
    ]
    
    print("MaxSim Population Averages:")
    for m in metrics:
        print(f"  {m}: {feat_maxsim[m].mean():.4f}")
        
    print("\nTop-5 Mean Population Averages:")
    for m in metrics:
        print(f"  {m}: {feat_top5mean[m].mean():.4f}")
        
    # Check if Top-5 Mean is starving Search/Retrieval
    search_maxsim = (feat_maxsim['retrieval_experience_score'] + feat_maxsim['ranking_experience_score']).mean()
    search_top5mean = (feat_top5mean['retrieval_experience_score'] + feat_top5mean['ranking_experience_score']).mean()
    
    print(f"\nTotal Search/Ranking Signal - MaxSim: {search_maxsim:.4f}")
    print(f"Total Search/Ranking Signal - Top-5 Mean: {search_top5mean:.4f}")

if __name__ == "__main__":
    main()
