import json
import pandas as pd
from engine import RankingEngine

engine = RankingEngine()

jd = {
    'family': 'Sales Manager',
    'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
    'title_terms': ["Sales Manager", "Account Executive", "Business Development Manager", "Sales Director", "VP of Sales", "Revenue Manager"],
    'req_skills': ["sales", "b2b", "crm", "salesforce", "hubspot", "quota", "pipeline", "outbound", "inbound", "lead generation", "negotiation", "closing", "prospecting", "account management"]
}

results = engine.run_pipeline(jd)
top100 = results[:100]

print("=== SECTION 1 & 2: Top 20 Candidates ===")
candidate_ids = [c['candidate_id'] for c in top100]
df_top = engine.df[engine.df['candidate_id'].isin(candidate_ids)].copy()
df_top.set_index('candidate_id', inplace=True)

for i, c in enumerate(top100[:20]):
    cid = c['candidate_id']
    row = df_top.loc[cid]
    skills = [s['name'].lower() for s in row.get('skills', [])] if isinstance(row.get('skills'), list) else []
    career = row.get('career_history', []) if isinstance(row.get('career_history'), list) else []
    
    matched_skills = [s for s in jd['req_skills'] if s in skills]
    career_titles = [str(job.get('title', '')).lower() for job in career]
    
    print(f"\n{i+1}. {cid} | {c['title']} | Score: {c['final_score']:.3f}")
    print(f"  Title Affinity:  {c['TitleAff_Contrib']:.3f}")
    print(f"  Skill Affinity:  {c['SkillAff_Contrib']:.3f}")
    print(f"  Career Affinity: {c['CareerAff_Contrib']:.3f}")
    print(f"  Semantic Sim:    {c['SemSim_Contrib']:.3f}")
    print(f"  BM25:            {c['BM25_Contrib']:.3f}")
    print(f"  Penalty:         {c['Penalties']:.3f}")
    print(f"  Matched Skills ({len(matched_skills)}): {matched_skills}")
    print(f"  Career History: {career_titles}")

print("\n=== SECTION 3: Highest-Ranked Specific Titles ===")
titles_to_find = [
    'sales manager', 'sales executive', 'account executive', 
    'business development manager', 'revenue operations manager', 
    'customer success manager'
]

found = {t: None for t in titles_to_find}
for i, c in enumerate(results):
    t = str(c['title']).lower().strip()
    if t in found and found[t] is None:
        found[t] = (i+1, c['candidate_id'], c['final_score'])
        
for t, res in found.items():
    if res:
        print(f"'{t}': Rank {res[0]} (ID: {res[1]}, Score: {res[2]:.3f})")
    else:
        print(f"'{t}': Not in Top 1000 retrieved")

print("\n=== SECTION 4: Top 100 Title Distribution ===")
counts = {
    'Sales': 0, 'Marketing': 0, 'Operations': 0, 
    'Finance': 0, 'HR': 0, 'Engineering': 0, 'Other': 0
}

for c in top100:
    t = str(c['title']).lower()
    if any(x in t for x in ['sales', 'account', 'business development', 'revenue', 'customer success']):
        counts['Sales'] += 1
    elif 'marketing' in t or 'seo' in t or 'content' in t:
        counts['Marketing'] += 1
    elif 'operations' in t or 'supply chain' in t:
        counts['Operations'] += 1
    elif 'accountant' in t or 'finance' in t or 'financial' in t or 'auditor' in t:
        counts['Finance'] += 1
    elif 'hr' in t or 'human resources' in t or 'recruiter' in t or 'talent' in t:
        counts['HR'] += 1
    elif 'engineer' in t or 'developer' in t or 'data' in t:
        counts['Engineering'] += 1
    else:
        counts['Other'] += 1

for k, v in counts.items():
    print(f"{k}: {v}")
