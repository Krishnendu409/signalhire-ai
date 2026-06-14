import json
import time
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
dataset_path = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"

texts = []
with open(dataset_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 1000: break
        c = json.loads(line)
        desc = " ".join([r.get('description', '') for r in c.get('career_history', [])])
        skills = " ".join([s.get('name', '') for s in c.get('skills', [])])
        texts.append(f"{c['profile'].get('current_title', '')} {skills} {desc}")

start = time.time()
embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
dur = time.time() - start

print(f"Time to embed 1000 candidates: {dur:.2f} seconds")
print(f"Estimated time for 116,000 candidates: {dur * 116.0 / 60.0:.2f} minutes")
