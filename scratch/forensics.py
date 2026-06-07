import json
import re

def run_forensics():
    path = r"C:\Users\krish\Documents\signalhire\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
    
    counts = {
        'total': 0,
        'retrieval': 0,
        'ranking': 0,
        'vector_db': 0,
        'evaluation': 0,
        'research_only': 0,
        'langchain_only': 0,
        'architect_no_code': 0
    }
    
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
                
            counts['total'] += 1
            
            profile = cand.get('profile', {}) or {}
            career = cand.get('career_history', []) or []
            skills = cand.get('skills', []) or []
            
            headline = profile.get('headline', '') or ''
            summary = profile.get('summary', '') or ''
            skills_text = " ".join([s.get('name', '') for s in skills])
            
            current_job = ""
            if career:
                current_job = ((career[0].get('title', '') or '') + " " + (career[0].get('description', '') or '')).lower()
                
            full_text = (headline + " " + summary + " " + current_job + " " + skills_text).lower()
            
            if re.search(r'\b(retrieval|semantic search)\b', full_text):
                counts['retrieval'] += 1
            if re.search(r'\b(ranking|learning to rank|recommender)\b', full_text):
                counts['ranking'] += 1
            if re.search(r'\b(pinecone|qdrant|milvus|weaviate|faiss)\b', full_text):
                counts['vector_db'] += 1
            if re.search(r'\b(ndcg|mrr|mean reciprocal rank)\b', full_text):
                counts['evaluation'] += 1
                
            # Disqualifiers
            if 'research' in current_job and not re.search(r'\b(production|deploy|serving)\b', current_job):
                counts['research_only'] += 1
            if 'langchain' in full_text and not re.search(r'\b(pytorch|tensorflow|keras|model)\b', full_text):
                counts['langchain_only'] += 1
            if 'architect' in current_job and not re.search(r'\b(code|hands-on|develop|programming|python|java|c\+\+)\b', current_job):
                counts['architect_no_code'] += 1
                
    print("Dataset Forensics (10k sample):")
    for k, v in counts.items():
        print(f"  {k}: {v} ({(v/counts['total'])*100:.2f}%)")

if __name__ == "__main__":
    run_forensics()
