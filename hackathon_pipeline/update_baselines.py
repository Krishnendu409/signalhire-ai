import pandas as pd
import json
import os
from engine import RankingEngine

engine = RankingEngine()
base_jds = {
    'Search Engineer': {
        'family': 'Search Engineer',
        'keywords': ['faiss', 'pinecone', 'elasticsearch', 'search', 'ranking', 'retrieval', 'machine learning', 'python'],
        'title_terms': engine.config['role_families']['Search Engineer'],
        'req_skills': engine.config['skill_families']['Search Engineer']
    },
    'Frontend Engineer': {
        'family': 'Frontend Engineer',
        'keywords': ['react', 'vue', 'css', 'html', 'javascript', 'frontend', 'ui', 'typescript'],
        'title_terms': engine.config['role_families']['Frontend Engineer'],
        'req_skills': engine.config['skill_families']['Frontend Engineer']
    },
    'Sales Manager': {
        'family': 'Sales Manager',
        'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
        'title_terms': engine.config['role_families']['Sales Manager'],
        'req_skills': engine.config['skill_families']['Sales Manager']
    }
}

os.makedirs('archive_v1_frozen', exist_ok=True)
for jd_name, jd_data in base_jds.items():
    print(f"Running pipeline for {jd_name}...")
    outputs = engine.run_pipeline(jd_data)
    baseline_path = os.path.join("archive_v1_frozen", f"top100_{jd_name.replace(' ', '_')}.json")
    with open(baseline_path, 'w') as f:
        json.dump(outputs, f, indent=2)
print("Updated all baselines.")
