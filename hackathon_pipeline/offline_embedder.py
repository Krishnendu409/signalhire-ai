import json
import time
import os
import numpy as np
from sentence_transformers import SentenceTransformer


def process_candidates(input_path, output_path):
    print("Loading all-MiniLM-L6-v2 model (optimized for CPU)...")
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

            # FIX: Extract from nested 'profile' object
            profile = cand.get('profile', {}) or {}
            headline = profile.get('headline', '') or ''
            summary = profile.get('summary', '') or ''
            current_title = profile.get('current_title', '') or ''

            # Skills and career are top-level
            skills = " ".join([s.get('name', '') for s in (cand.get('skills', []) or [])])
            career = " ".join([
                (c.get('title', '') or '') + " " + (c.get('description', '') or '')
                for c in (cand.get('career_history', []) or [])
            ])

            # Construct a rich text representation including headline + summary
            full_text = f"{headline} | {current_title} | {summary} {skills} {career}".strip()
            texts_batch.append(full_text)

            if len(texts_batch) >= batch_size:
                total = len(ids) + len(texts_batch)
                print(f"Embedding batch of {batch_size}... (Total processed: {total})")
                batch_embs = model.encode(texts_batch, convert_to_numpy=True)
                # Cast to float16 to save memory & disk space
                embeddings.append(batch_embs.astype(np.float16))
                ids.extend(ids_batch)
                texts_batch = []
                ids_batch = []

        # Process remaining
        if texts_batch:
            total = len(ids) + len(texts_batch)
            print(f"Embedding final batch... (Total processed: {total})")
            batch_embs = model.encode(texts_batch, convert_to_numpy=True)
            embeddings.append(batch_embs.astype(np.float16))
            ids.extend(ids_batch)

    if not embeddings:
        print("No embeddings generated.")
        return

    final_embeddings = np.vstack(embeddings)

    elapsed = time.time() - start_time
    print(f"Finished embedding {len(ids)} candidates in {elapsed:.2f} seconds.")
    print(f"Saving to {output_path} (shape: {final_embeddings.shape})")

    np.save(output_path, final_embeddings)
    np.save("candidate_ids.npy", np.array(ids))


if __name__ == "__main__":
    input_file = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
    
    output_file = "candidate_embeddings.npy"
    process_candidates(input_file, output_file)
