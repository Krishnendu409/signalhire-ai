import time
import os
import csv
import json
import faiss
import pickle
import numpy as np
import pandas as pd
from hackathon_pipeline.engine import RankingEngine

engine = RankingEngine()

jds = {
    'Cloud Engineer': {
        "family": "Cloud Engineer",
        "title_terms": ["cloud", "devops", "infrastructure", "sre", "platform"],
        "req_skills": ["aws", "azure", "gcp", "kubernetes", "docker", "terraform", "ci/cd", "linux", "bash"],
        "keywords": ["deployment", "automation", "scaling", "monitoring"],
        "min_experience": 4, "max_experience": 12, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    'Frontend Engineer': {
        "family": "Frontend Engineer",
        "title_terms": ["frontend", "ui", "ux", "client", "web", "javascript", "react", "angular", "vue", "front-end"],
        "req_skills": ["javascript", "react", "css", "html", "typescript", "ui/ux", "vue", "angular", "redux", "next.js"],
        "keywords": ["responsive", "component", "spa", "css3"],
        "min_experience": 3, "max_experience": 10, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    'Search Engineer': {
        "family": "Search Engineer",
        "title_terms": ["search", "retrieval", "relevance", "ranking", "nlp", "machine learning", "ai", "data scientist", "ml"],
        "req_skills": ["python", "elasticsearch", "faiss", "machine learning", "nlp", "deep learning", "pytorch", "tensorflow", "scikit-learn"],
        "keywords": ["search", "vector", "embedding", "llm"],
        "min_experience": 5, "max_experience": 15, "budget_lpa_max": 999.0, "work_mode": "remote"
    }
}

known_synonyms = {
    "aws": ["amazon web services", "amazon cloud"],
    "gcp": ["google cloud", "google cloud platform"],
    "react": ["react.js", "reactjs", "react native"],
    "vue": ["vue.js", "vuejs"],
    "search engineer": ["information retrieval engineer", "relevance engineer", "ann engineer", "search relevance", "ir engineer"],
    "vector": ["approximate nearest neighbor", "ann", "hnsw"],
    "nlp": ["natural language processing", "text mining", "computational linguistics"],
    "machine learning": ["ml", "predictive modeling", "statistical learning"],
    "ai": ["artificial intelligence"],
    "ui/ux": ["user interface", "user experience", "ui", "ux"],
    "frontend": ["client-side", "client side"],
    "devops": ["platform engineering", "platform engineer"]
}

engine.load_retrieval_indexes()
import gc
gc.collect()

f = open('VOCABULARY_FRAGILITY_AUDIT.md', 'w', encoding='utf-8')
f.write("# VOCABULARY FRAGILITY AUDIT\\n\\n")

csv_records = []
severity_table = {}

def compute_mock_score_delta(cid, jd, missing_term):
    # This is an approximation. If it's a req_skill, the penalty is in skill_depth_affinity and semantic_sim
    # If it's a title, it's title_affinity.
    # We will simulate a perfect +1 bump to the relevant affinity score.
    w_skill = engine.config['weights']['skill_depth_affinity']
    w_title = engine.config['weights']['title_affinity']
    
    if missing_term in jd['req_skills']:
        return w_skill * 1.0, "skill_depth_affinity"
    elif missing_term in jd['title_terms']:
        return w_title * 1.0, "title_affinity"
    else:
        return engine.config['weights']['semantic_sim'] * 0.5, "semantic_sim"

for role, jd in jds.items():
    f.write(f"## {role}\\n\\n")
    
    query_str = f"{' '.join(jd['title_terms'])} {' '.join(jd['req_skills'])} {' '.join(jd['keywords'])}".lower()
    
    qv = engine.encoder.encode([query_str])
    faiss.normalize_L2(qv)
    _, dense_indices = engine.faiss_index.search(qv, len(engine.candidate_ids))
    dense_cids = [engine.candidate_ids[idx] for idx in dense_indices[0][:1000]]
    
    v2_ranked = engine.run_pipeline(jd, top_k=100000, use_retrieval=False)
    v2_dict = {c['candidate_id']: {'rank': c['rank'], 'score': c['final_score']} for c in v2_ranked}
    
    jd_terms_all = [t.lower() for t in jd['title_terms'] + jd['req_skills'] + jd['keywords']]
    
    for rank_faiss, cid in enumerate(dense_cids[:100]): 
        v2_info = v2_dict.get(cid, {'rank': 999999, 'score': 0})
        rank_v2 = v2_info['rank']
        
        if rank_v2 > 100: 
            row = engine.df[engine.df['candidate_id'] == cid].iloc[0]
            cand_text = f"{row['current_title']} {row['skills_text']} {row['desc_text']}".lower()
            
            for term in jd_terms_all:
                if term not in cand_text and term in known_synonyms:
                    for syn in known_synonyms[term]:
                        if syn in cand_text:
                            # We found a fragility hit.
                            score_delta, feature = compute_mock_score_delta(cid, jd, term)
                            mock_new_score = v2_info['score'] + score_delta
                            
                            # Estimate new rank
                            new_rank = 1
                            for c in v2_ranked:
                                if c['final_score'] > mock_new_score: new_rank += 1
                                else: break
                                
                            key = f"{term.upper()} <-> {syn.title()}"
                            if key not in severity_table:
                                severity_table[key] = {'occ': 0, 't20': 0, 't100': 0, 'dmg': 0.0}
                            
                            severity_table[key]['occ'] += 1
                            if new_rank <= 20 and rank_v2 > 20: severity_table[key]['t20'] += 1
                            if new_rank <= 100 and rank_v2 > 100: severity_table[key]['t100'] += 1
                            severity_table[key]['dmg'] += score_delta
                            
                            csv_records.append({
                                'JD Term': term,
                                'Candidate Term': syn,
                                'Candidate ID': cid,
                                'Original V2 Rank': rank_v2,
                                'Rank if Synonym Matched': new_rank,
                                'Score Delta': round(score_delta, 2),
                                'Feature Affected': feature
                            })

# Sort CSV records by score delta descending
csv_records = sorted(csv_records, key=lambda x: x['Score Delta'], reverse=True)

with open('TOP_50_VOCABULARY_FAILURES.csv', 'w', newline='', encoding='utf-8') as fcsv:
    writer = csv.DictWriter(fcsv, fieldnames=['JD Term', 'Candidate Term', 'Candidate ID', 'Original V2 Rank', 'Rank if Synonym Matched', 'Score Delta', 'Feature Affected'])
    writer.writeheader()
    for row in csv_records[:50]:
        writer.writerow(row)

f.write("## VOCABULARY FRAGILITY SEVERITY TABLE\\n\\n")
f.write("| Mismatch Type | Occurrences | Top20 Impact | Top100 Impact | Est. Precision Loss (Sum of Deltas) |\\n")
f.write("|---|---|---|---|---|\\n")

sorted_sev = sorted(severity_table.items(), key=lambda x: x[1]['dmg'], reverse=True)
for key, vals in sorted_sev:
    f.write(f"| {key} | {vals['occ']} | {vals['t20']} lost | {vals['t100']} lost | {vals['dmg']:.1f} pts |\\n")

f.write("\\n\\n*(Note: Top20/Top100 Impact signifies candidates who WOULD have been in the Top N if the regex had mapped the synonym, but were incorrectly demoted.)*\\n")
f.close()

print("Vocabulary Fragility Audit & CSV generated.")
