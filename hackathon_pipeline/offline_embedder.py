import json
import time
import os
import numpy as np
from sentence_transformers import SentenceTransformer

def process_candidates(input_path, output_path):
    print("Loading all-MiniLM-L6-v2 model (optimized for CPU)...")
    # This model is fast and produces 384-dimensional embeddings
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    embeddings = []
    ids = []
    
    print(f"Reading {input_path}...")
    start_time = time.time()
    
    batch_size = 2000
    texts_batch = []
    ids_batch = []
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return
        
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                cand = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            ids_batch.append(cand.get('candidate_id'))
            
            # Construct a dense text representation
            summary = cand.get('summary', '') or ''
            skills = " ".join([s.get('name', '') for s in cand.get('skills', [])])
            career = " ".join([c.get('description', '') or '' for c in cand.get('career_history', [])])
            
            full_text = f"{summary} {skills} {career}".strip()
            texts_batch.append(full_text)
            
            if len(texts_batch) >= batch_size:
                print(f"Embedding batch of {batch_size}... (Total processed: {len(embeddings)*batch_size + len(texts_batch)})")
                # convert_to_numpy=True is default, but explicit is better
                batch_embs = model.encode(texts_batch, convert_to_numpy=True)
                # Cast to float16 to save memory & disk space (75MB total instead of 150MB)
                embeddings.append(batch_embs.astype(np.float16))
                ids.extend(ids_batch)
                texts_batch = []
                ids_batch = []
                
        # Process remaining
        if texts_batch:
            batch_embs = model.encode(texts_batch, convert_to_numpy=True)
            embeddings.append(batch_embs.astype(np.float16))
            ids.extend(ids_batch)

    if not embeddings:
        print("No embeddings generated.")
        return

    final_embeddings = np.vstack(embeddings)
    
    print(f"Finished embedding {len(ids)} candidates in {time.time() - start_time:.2f} seconds.")
    print(f"Saving to {output_path} (shape: {final_embeddings.shape})")
    
    # Save embeddings matrix and the corresponding ID map
    np.save(output_path, final_embeddings)
    with open(output_path.replace('.npy', '_ids.json'), 'w') as f:
        json.dump(ids, f)
        
if __name__ == "__main__":
    # Adjust path if running from root or hackathon_pipeline dir
    input_file = r"../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
    if not os.path.exists(input_file):
        input_file = r"[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
        
    output_file = "candidate_embeddings.npy"
    process_candidates(input_file, output_file)
