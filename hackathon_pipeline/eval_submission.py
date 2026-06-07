import pandas as pd
import json

print("Evaluating submission.csv...")

sub = pd.read_csv("submission.csv")
top100_ids = set(sub['candidate_id'].tolist())

# Read full dataset for ground truth
input_file = r"C:\Users\krish\Downloads\signalhire-ai-master (3)\signalhire-ai-master\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
records = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                records.append(json.loads(line))
            except:
                pass

df = pd.DataFrame(records)
df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in df['career_history']]

search_mask = df['current_title'].str.contains('search engineer', case=False)
retrieval_mask = df['current_title'].str.contains('retrieval engineer', case=False)
nlp_mask = df['current_title'].str.contains('nlp engineer', case=False)
ranking_mask = df['current_title'].str.contains('ranking engineer|ml ranking', case=False)

all_relevant_mask = search_mask | retrieval_mask | nlp_mask | ranking_mask
relevant_ids = set(df[all_relevant_mask]['candidate_id'].tolist())

# Join submission with df to get titles and skills
top100 = df[df['candidate_id'].isin(top100_ids)].copy()
top100 = pd.merge(sub, top100, on='candidate_id', how='left')

# Recall @ 100
overlap = len(top100_ids.intersection(relevant_ids))
recall_100 = overlap / len(relevant_ids) if len(relevant_ids) > 0 else 0

# Penetration
# Honeypots have high vector db score but non-engineering titles or zero relevance
trap_titles = ['marketing', 'sales', 'hr', 'recruiter', 'manager', 'project manager', 'product manager', 'analyst', 'support', 'executive', 'director']
is_non_eng = top100['current_title'].apply(lambda t: any(tr in t for tr in trap_titles) and 'engineer' not in t)
honeypots = top100[is_non_eng]

print(f"Recall@100: {recall_100*100:.1f}% ({overlap}/{len(relevant_ids)})")
print(f"Honeypot Penetration: {len(honeypots)}%")
print("\nTop 20 Titles:")
print(top100.head(20)['current_title'].value_counts())

all_skills = []
for s_list in top100.head(20)['skills']:
    if isinstance(s_list, list):
        for s in s_list:
            if isinstance(s, dict) and s.get('name'):
                all_skills.append(s['name'].lower())

from collections import Counter
print("\nTop 20 Skills:")
print(pd.Series(Counter(all_skills)).sort_values(ascending=False).head(20))
