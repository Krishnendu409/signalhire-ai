import json
import re

def inspect_ndcg():
    path = r"C:\Users\krish\Documents\signalhire\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
    
    found = []
    
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 10000:
                break
            if not line.strip():
                continue
            try:
                cand = json.loads(line)
            except:
                continue
                
            profile = cand.get('profile', {}) or {}
            career = cand.get('career_history', []) or []
            skills = cand.get('skills', []) or []
            
            headline = profile.get('headline', '') or ''
            summary = profile.get('summary', '') or ''
            skills_text = " ".join([s.get('name', '') for s in skills])
            
            current_job = ""
            past_jobs = ""
            if career:
                current_job = ((career[0].get('title', '') or '') + " " + (career[0].get('description', '') or '')).lower()
                if len(career) > 1:
                    past_jobs = " ".join([((j.get('title', '') or '') + " " + (j.get('description', '') or '')) for j in career[1:]]).lower()
                
            full_text = (headline + " " + summary + " " + current_job + " " + past_jobs + " " + skills_text).lower()
            
            if re.search(r'\b(ndcg|mrr|mean reciprocal rank)\b', full_text):
                found.append({
                    'id': cand.get('candidate_id'),
                    'title': profile.get('current_title'),
                    'headline': headline,
                    'summary': summary,
                    'current_job': current_job
                })
                
    print(f"Found {len(found)} candidates mentioning evaluation metrics:")
    for i, c in enumerate(found):
        print(f"\n--- Candidate {i+1} ---")
        print(f"Title: {c['title']}")
        print(f"Headline: {c['headline']}")
        print(f"Summary: {c['summary'][:200]}...")
        print(f"Job Snippet: {c['current_job'][:200]}...")

if __name__ == "__main__":
    inspect_ndcg()
