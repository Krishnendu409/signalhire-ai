from hackathon_pipeline.engine import RankingEngine
from collections import Counter
engine = RankingEngine()
jds = [
    {'family': 'Sales Executive', 'title_terms': ['sales', 'executive', 'account'], 'req_skills': ['b2b', 'negotiation', 'crm'], 'keywords': ['sales', 'quota', 'b2b']},
    {'family': 'Cloud Engineer', 'title_terms': ['cloud', 'aws', 'azure'], 'req_skills': ['aws', 'terraform', 'kubernetes'], 'keywords': ['cloud', 'infrastructure']},
    {'family': 'Data Analyst', 'title_terms': ['data', 'analyst'], 'req_skills': ['sql', 'tableau', 'excel', 'python'], 'keywords': ['data', 'analytics', 'dashboard']},
    {'family': 'HR Manager', 'title_terms': ['hr', 'human resources', 'manager'], 'req_skills': ['recruitment', 'employee relations'], 'keywords': ['hr', 'talent']},
    {'family': 'Content Writer', 'title_terms': ['content', 'writer', 'copywriter'], 'req_skills': ['seo', 'writing', 'editing'], 'keywords': ['content', 'blog', 'seo']}
]

print('\n=== SALES PIPELINE REGRESSION ===')
res = engine.run_pipeline(jds[0], top_k=20)
titles = [c['title'] for c in res]
print(Counter(titles))

print('\n=== RANDOM JD TESTING ===')
for jd in jds[1:]:
    print(f"\nJD: {jd['family']}")
    res = engine.run_pipeline(jd, top_k=10)
    print(Counter([c['title'] for c in res]))
