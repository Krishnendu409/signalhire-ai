import json
import faiss
import numpy as np
import pickle
import time
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

dataset_path = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
bm25_path = r"C:\Users\krish\Documents\signalhire\hackathon_pipeline\bm25_index.pkl"
faiss_path = r"C:\Users\krish\Documents\signalhire\hackathon_pipeline\faiss_index.bin"
metadata_path = r"C:\Users\krish\Documents\signalhire\hackathon_pipeline\index_metadata.pkl"

print("Loading sentence-transformers model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

candidates = []
texts = []
tokenized_texts = []
candidate_ids = []

print("Reading dataset...")
with open(dataset_path, 'r', encoding='utf-8') as f:
    for line in f:
        c = json.loads(line)
        cid = c['candidate_id']
        desc = " ".join([r.get('description', '') for r in c.get('career_history', [])])
        skills = " ".join([s.get('name', '') for s in c.get('skills', [])])
        title = c['profile'].get('current_title', '')
        
        full_text = f"{title} {skills} {desc}".lower()
        
        candidate_ids.append(cid)
        texts.append(full_text)
        tokenized_texts.append(full_text.split())
        
print(f"Loaded {len(texts)} candidates.")

print("Building BM25 Index...")
start_time = time.time()
bm25 = BM25Okapi(tokenized_texts)
print(f"BM25 built in {time.time() - start_time:.2f}s")

with open(bm25_path, 'wb') as f:
    pickle.dump(bm25, f)

print("Building FAISS Index...")
start_time = time.time()
# Encode in batches
embeddings = model.encode(texts, batch_size=64, show_progress_bar=True)
print(f"Embeddings generated in {time.time() - start_time:.2f}s")

# Inner product index (since all-MiniLM-L6-v2 produces normalized vectors, IP == Cosine Sim)
index = faiss.IndexFlatIP(384)
faiss.normalize_L2(embeddings)
index.add(embeddings)

faiss.write_index(index, faiss_path)

with open(metadata_path, 'wb') as f:
    pickle.dump(candidate_ids, f)

print("Done. Saved all indexes.")
