import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import zipfile
import xml.etree.ElementTree as ET
import os

def get_docx_text(path):
    z = zipfile.ZipFile(path)
    xml_content = z.read('word/document.xml')
    z.close()
    tree = ET.XML(xml_content)
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join(''.join(n.text for n in p.iter(w + 't') if n.text) for p in tree.iter(w + 'p') if any(n.text for n in p.iter(w + 't')))

def find_elite_candidates(cands_path, max_cands=10000):
    elite = []
    corpus_texts = []
    cands_data = []
    
    with open(cands_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= max_cands: break
            if not line.strip(): continue
            try:
                c = json.loads(line)
                cands_data.append(c)
                
                # Combine text
                p = c.get('profile', {}) or {}
                headline = p.get('headline', '') or ''
                summary = p.get('summary', '') or ''
                title = p.get('current_title', '') or ''
                
                skills = " ".join([s.get('name', '') for s in (c.get('skills', []) or [])])
                career = " ".join([(j.get('title', '') or '') + " " + (j.get('description', '') or '') for j in (c.get('career_history', []) or [])])
                
                full_text = f"{headline} {summary} {title} {skills} {career}"
                corpus_texts.append(full_text)
                
                t_lower = title.lower()
                company_lower = " ".join([j.get('company', '') for j in (c.get('career_history', []) or [])]).lower()
                
                # Find some specific elites
                is_elite = False
                if 'google' in company_lower and ('search' in t_lower or 'nlp' in t_lower or 'machine learning' in t_lower):
                    is_elite = True
                elif 'apple' in company_lower and ('ai' in t_lower or 'machine learning' in t_lower or 'nlp' in t_lower):
                    is_elite = True
                elif 'netflix' in company_lower and ('nlp' in t_lower or 'recommendation' in t_lower or 'machine learning' in t_lower):
                    is_elite = True
                elif 'linkedin' in company_lower and ('ml' in t_lower or 'ranking' in t_lower or 'machine learning' in t_lower or 'search' in t_lower):
                    is_elite = True
                
                if is_elite and len(elite) < 10:
                    elite.append({
                        'candidate_id': c['candidate_id'],
                        'title': title,
                        'company': 'Google' if 'google' in company_lower else 'Apple' if 'apple' in company_lower else 'Netflix' if 'netflix' in company_lower else 'LinkedIn' if 'linkedin' in company_lower else 'Elite',
                        'index': len(corpus_texts) - 1
                    })
                    
            except Exception as e:
                pass
                
    return elite, corpus_texts, cands_data

def run_experiment():
    print("Loading data...")
    cands_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(cands_path):
        cands_path = r"../" + cands_path
        
    jd_path = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/job_description.docx"
    if not os.path.exists(jd_path):
        jd_path = r"../" + jd_path
        
    jd_text = get_docx_text(jd_path)
    
    elite, corpus_texts, cands_data = find_elite_candidates(cands_path, max_cands=100000)
    print(f"Found {len(elite)} elite candidates.")
    for e in elite:
        print(f"  - {e['candidate_id']}: {e['title']} ({e['company']})")
        
    # We will compute embeddings for a subset if doing all 100k is too slow, but we can load the precomputed ones!
    # Let's load the precomputed ones to save time, but wait, precomputed ones don't have skills/career in them!
    # So the semantic retrieval ITSELF was flawed because the precomputed embeddings only used headline+summary+title!
    # Let's re-embed the 100k full texts? No, too slow.
    # The user asked: "Take your known elite candidates. Test: MaxSim Rank, MeanSim Rank, Top-K Mean Rank."
    # If the candidate embeddings were truncated/missing skills, then their rank is bad anyway.
    # I should re-compute embeddings for just these 10000 candidates with full text.
    print("Encoding 10,000 candidates with FULL TEXT (headline+summary+title+skills+career)...")
    corpus_texts_subset = corpus_texts[:10000]
    
    # Wait, if we only use 10,000, ranks will be out of 10,000. That's fine for comparison.
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    doc_embs = embedder.encode(corpus_texts_subset, convert_to_numpy=True, show_progress_bar=True).astype(np.float16)
    
    # JD Chunks
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
    # shape: (num_docs, num_chunks)
    sim_matrix = doc_embs.dot(chunk_embs.T)
    
    max_sims = np.max(sim_matrix, axis=1)
    mean_sims = np.mean(sim_matrix, axis=1)
    
    # Top 3 mean
    # sort the chunks for each doc, take top 3, then mean
    sorted_sims = np.sort(sim_matrix, axis=1)[:, ::-1]
    top3_mean_sims = np.mean(sorted_sims[:, :3], axis=1)
    
    # Top 5 mean
    top5_mean_sims = np.mean(sorted_sims[:, :5], axis=1)
    
    print("\n" + "="*50)
    print("ELITE CANDIDATE RECALL AUDIT (Ranks out of 10,000)")
    print("="*50)
    
    for e in elite:
        idx = e['index']
        if idx >= 10000: continue
        
        max_rank = np.sum(max_sims > max_sims[idx]) + 1
        mean_rank = np.sum(mean_sims > mean_sims[idx]) + 1
        top3_rank = np.sum(top3_mean_sims > top3_mean_sims[idx]) + 1
        top5_rank = np.sum(top5_mean_sims > top5_mean_sims[idx]) + 1
        
        print(f"\n{e['candidate_id']} - {e['title']} ({e['company']})")
        print(f"MaxSim: {max_rank}")
        print(f"MeanSim: {mean_rank}")
        print(f"Top-3 Mean: {top3_rank}")
        print(f"Top-5 Mean: {top5_rank}")

if __name__ == "__main__":
    run_experiment()
