import json
import pandas as pd
import numpy as np
import lightgbm as lgb
from feature_extractor import extract_recruiter_features, FEATURE_COLS

print("Running Search Engineer Inference using V2 Model...")

input_file = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
records = []

# Load candidates
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                records.append(json.loads(line))
            except:
                pass

df = pd.DataFrame(records)

# We use simple exact matching to simulate the top BM25 candidates for a Search Engineer
# A real Search Engineer JD demands faiss, pinecone, elasticsearch
def search_relevance(row):
    skills = [s.get('name', '').lower() for s in row.get('skills', []) if isinstance(s, dict)]
    ch = row.get('career_history', [])
    desc = ch[0].get('description', '').lower() if ch else ''
    title = ch[0].get('title', '').lower() if ch else ''
    
    score = 0
    if 'faiss' in skills or 'pinecone' in skills or 'elasticsearch' in skills:
        score += 5
    if 'engineer' in title or 'developer' in title:
        score += 2
    if 'search' in desc or 'ranking' in desc or 'retrieval' in desc:
        score += 3
    return score

df['search_rel'] = df.apply(search_relevance, axis=1)

# Grab top 5000 by relevance (simulated retrieval)
top_5000 = df.nlargest(5000, 'search_rel').copy()

print("Extracting features for Top 5000...")
features_df = extract_recruiter_features(top_5000)

# Simulate retrieval scores for the top candidates
np.random.seed(42)
features_df['semantic_sim'] = np.random.uniform(0.7, 1.0, size=len(features_df))
features_df['bm25_score'] = np.random.uniform(0.5, 1.0, size=len(features_df))

print("Loading V2 Model...")
model = lgb.Booster(model_file="lgbm_ranker_v2.txt")
features_df['score'] = model.predict(features_df[FEATURE_COLS])

# Attach IDs and text
features_df['candidate_id'] = top_5000['candidate_id'].values
features_df['career_history'] = top_5000['career_history'].values
features_df['skills'] = top_5000['skills'].values

# Get Top 20
top_20 = features_df.nlargest(20, 'score')

report = "# Top 20 Candidates for Search Engineer JD (V2 Model)\n\n"
for i, (idx, row) in enumerate(top_20.iterrows()):
    skills_list = [s.get('name', '') for s in row['skills'] if isinstance(s, dict)]
    ch = row['career_history']
    desc = ch[0].get('description', '') if ch else ''
    
    report += f"### {i+1}. {row['candidate_id']}\n"
    report += f"* **Title:** {row['current_title']}\n"
    report += f"* **Score:** {row['score']:.4f}\n"
    report += f"* **Domain Authenticity:** {row['domain_authenticity_score']:.1f} | **Vector DB:** {row['vector_db_score']:.1f} | **Trap Risk:** {row['keyword_trap_risk']:.1f}\n"
    report += f"* **Top Skills:** {', '.join(skills_list[:7])}\n"
    report += f"* **Snippet:** \"{desc[:200]}...\"\n\n"

with open("top20_search_engineer.md", "w", encoding="utf-8") as f:
    f.write(report)
print("Top 20 written to top20_search_engineer.md")
