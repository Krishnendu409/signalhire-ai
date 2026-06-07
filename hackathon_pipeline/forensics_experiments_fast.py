import json
import pandas as pd
import numpy as np
import copy
import re
import time
from engine import RankingEngine

print("Loading data...")
engine = RankingEngine()

jd = {
    'family': 'Sales Manager',
    'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
    'title_terms': ["Sales Manager", "Account Executive", "Business Development Manager", "Sales Director", "VP of Sales", "Revenue Manager"],
    'req_skills': ["sales", "b2b", "crm", "salesforce", "hubspot", "quota", "pipeline", "outbound", "inbound", "lead generation", "negotiation", "closing", "prospecting", "account management"]
}

print("Running baseline pipeline...")
results = engine.run_pipeline(jd)
df_feat = engine._extract_features(jd)
df_ranked = engine._rank_features(df_feat)

print("=== PART 1: QUESTIONS TO ANSWER ===")

# Q1: Variance of final score components for Top 100
top100_ranked = df_ranked.head(100)
var_metrics = {}
for col in ['title_affinity', 'skill_affinity', 'career_affinity', 'semantic_sim', 'bm25_score', 'quality_score', 'penalties']:
    weight = engine.config['weights'].get(col, 1.0) if col != 'penalties' else 1.0
    contribs = top100_ranked[col] * weight
    var_metrics[col] = np.var(contribs)

total_var = sum(var_metrics.values()) if sum(var_metrics.values()) > 0 else 1.0
print("\n1. Percentage of final score variance (Top 100):")
for col, v in var_metrics.items():
    print(f"  {col}: {(v/total_var)*100:.2f}%")

# Q2: Accountant at Rank #1
acc_id = results[0]['candidate_id']
acc_row = df_feat[df_feat['candidate_id'] == acc_id].iloc[0]

s_text = acc_row['skills_text']
d_text = acc_row['desc_text']
t_text = acc_row['current_title']

sk_hits = [k for k in jd['req_skills'] if k in s_text]
c_hits = [k for k in jd['keywords'] if k in d_text]

cand_t_fams = [(fam, [w for w in terms if w in t_text]) for fam, terms in engine.config['role_families'].items()]
cand_s_fams = [(fam, [w for w in terms if w in s_text]) for fam, terms in engine.config['skill_families'].items()]
cand_c_fams = [(fam, [w for w in terms if w in d_text]) for fam, terms in engine.config['skill_families'].items()]

print(f"\n2. For the Rank #1 ({acc_id}):")
print(f"  Raw Skill Affinity: {acc_row['skill_affinity']} -> Contrib: {acc_row['skill_affinity'] * engine.config['weights']['skill_affinity']}")
print(f"  Raw Career Affinity: {acc_row['career_affinity']} -> Contrib: {acc_row['career_affinity'] * engine.config['weights']['career_affinity']}")
print(f"  Exact Skill Tokens Matched: {sk_hits}")
print(f"  Exact Career Tokens Matched: {c_hits}")
print(f"  Dictionary role title matches: {[(f, hits) for f, hits in cand_t_fams if hits]}")

# Q3-Q6 overrides
print("\n3. If Title Affinity is forced to zero:")
df_no_title = df_feat.copy()
df_no_title['title_affinity'] = 0.0
ranked_no_title = engine._rank_features(df_no_title)
for i, (_, row) in enumerate(ranked_no_title.head(5).iterrows()):
    print(f"    {i+1}. {row['candidate_id']} | {row['current_title']} | Score: {row['final_score']:.3f}")

df_no_qual = df_feat.copy()
df_no_qual['quality_score'] = 0.0
ranked_no_qual = engine._rank_features(df_no_qual)
rank_acc_no_qual = np.where(ranked_no_qual['candidate_id'] == acc_id)[0][0] + 1
print(f"\n4. If Quality Score is removed: Rank #1 becomes rank #{rank_acc_no_qual}")

df_no_sk = df_feat.copy()
df_no_sk['skill_affinity'] = 0.0
ranked_no_sk = engine._rank_features(df_no_sk)
rank_acc_no_sk = np.where(ranked_no_sk['candidate_id'] == acc_id)[0][0] + 1
print(f"5. If Skill Affinity is removed: Rank #1 becomes rank #{rank_acc_no_sk}")

df_no_car = df_feat.copy()
df_no_car['career_affinity'] = 0.0
ranked_no_car = engine._rank_features(df_no_car)
rank_acc_no_car = np.where(ranked_no_car['candidate_id'] == acc_id)[0][0] + 1
print(f"6. If Career Affinity is removed: Rank #1 becomes rank #{rank_acc_no_car}")


print("\n=== PART 2: REQUIRED EXPERIMENTS ===")

class ExperimentEngine(RankingEngine):
    def __init__(self, mode='A'):
        super().__init__()
        self.mode = mode
        if mode in ['B', 'C']:
            for f in ['manager', 'executive', 'account', 'marketing']:
                if f in self.config['role_families']['Sales Manager']:
                    self.config['role_families']['Sales Manager'].remove(f)

    def _extract_features(self, jd_data):
        if self.mode in ['A', 'C']:
            feat = self.df[['candidate_id', 'current_title', 'quality_score', 'skills_text', 'skills', 'desc_text']].copy()
            jd_fam = jd_data['family']
            
            # PRECOMPILE REGEXES FOR PERFORMANCE
            # JD terms
            c_title_terms = [re.compile(r'\b' + re.escape(w) + r'\b') for w in jd_data['title_terms']]
            c_req_skills = [re.compile(r'\b' + re.escape(w) + r'\b') for w in jd_data['req_skills']]
            c_keywords = [re.compile(r'\b' + re.escape(w) + r'\b') for w in jd_data['keywords']]
            
            # Family Terms
            c_role_fams = {}
            for fam, terms in self.config['role_families'].items():
                c_role_fams[fam] = [re.compile(r'\b' + re.escape(w) + r'\b') for w in terms]
                
            c_skill_fams = {}
            for fam, terms in self.config['skill_families'].items():
                c_skill_fams[fam] = [re.compile(r'\b' + re.escape(w) + r'\b') for w in terms]

            len_req = max(len(jd_data['req_skills']), 1)
            len_key = max(len(jd_data['keywords']), 1)

            def ext_features_token(row):
                s_text = row['skills_text']
                d_text = row['desc_text']
                t_text = row['current_title']
                full = s_text + " " + d_text
                
                t_hits = sum(1 for p in c_title_terms if p.search(t_text))
                taff = min(t_hits / 2.0, 1.0)
                
                sk_hits = sum(1 for p in c_req_skills if p.search(s_text))
                saff = sk_hits / len_req
                
                c_hits = sum(1 for p in c_keywords if p.search(d_text))
                caff = c_hits / len_key
                
                hits = sum(1 for p in c_keywords if p.search(full))
                sem = hits / len_key
                bm25 = sem * 0.8
                
                cand_t_fam = max([(fam, sum(1 for p in patterns if p.search(t_text))) for fam, patterns in c_role_fams.items()], key=lambda x: x[1])
                cand_s_fam = max([(fam, sum(1 for p in patterns if p.search(s_text))) for fam, patterns in c_skill_fams.items()], key=lambda x: x[1])
                cand_c_fam = max([(fam, sum(1 for p in patterns if p.search(d_text))) for fam, patterns in c_skill_fams.items()], key=lambda x: x[1])
                
                t_fam = cand_t_fam[0] if cand_t_fam[1] > 0 else 'Unknown'
                s_fam = cand_s_fam[0] if cand_s_fam[1] > 0 else 'Unknown'
                c_fam = cand_c_fam[0] if cand_c_fam[1] > 0 else 'Unknown'
                
                is_consistent = (t_fam == jd_fam) and (s_fam == jd_fam) and (c_fam == jd_fam)
                is_inconsistent = (t_fam != jd_fam and t_fam != 'Unknown') and (s_fam != jd_fam and s_fam != 'Unknown') and (c_fam != jd_fam and c_fam != 'Unknown')
                is_partial = not is_consistent and not is_inconsistent
                
                return pd.Series([sem, bm25, taff, saff, caff, t_fam, s_fam, c_fam, is_consistent, is_inconsistent, is_partial])
                
            feat[['semantic_sim', 'bm25_score', 'title_affinity', 'skill_affinity', 'career_affinity', 't_fam', 's_fam', 'c_fam', 'is_consistent', 'is_inconsistent', 'is_partial']] = feat.apply(ext_features_token, axis=1)
            
            is_sales = (jd_fam == 'Sales Manager')
            if is_sales:
                feat['is_trap'] = feat['current_title'].str.contains('engineer|developer|scientist|data')
            else:
                feat['is_trap'] = feat['current_title'].apply(lambda t: any(tr in t for tr in self.config['trap_titles']) and 'engineer' not in t)
            return feat
        else:
            return super()._extract_features(jd_data)

def run_experiment(mode, jd_base):
    print(f"\n--- EXPERIMENT {mode} ---")
    st = time.time()
    eng = ExperimentEngine(mode=mode)
    res = eng.run_pipeline(jd_base)
    et = time.time()
    
    print(f"Runtime: {et - st:.2f}s")
    print("Top 5 candidates:")
    for i, c in enumerate(res[:5]):
        print(f"  {i+1}. {c['candidate_id']} | {c['title']} | Score: {c['final_score']:.3f}")
        
    counts = {'Sales': 0, 'HR': 0, 'Marketing': 0, 'Other': 0}
    for c in res[:100]:
        t = str(c['title']).lower()
        if any(x in t for x in ['sales', 'account executive', 'business development', 'revenue', 'customer success']):
            counts['Sales'] += 1
        elif 'hr' in t or 'human resources' in t or 'recruiter' in t:
            counts['HR'] += 1
        elif 'marketing' in t:
            counts['Marketing'] += 1
        else:
            counts['Other'] += 1
    print(f"Top 100 Distribution: Sales {counts['Sales']}%, HR {counts['HR']}%, Marketing {counts['Marketing']}%, Other {counts['Other']}%")
    
    titles = ['sales manager', 'sales executive', 'account executive', 'business development manager', 'revenue operations manager', 'customer success manager']
    found = {t: None for t in titles}
    for i, c in enumerate(res):
        t = str(c['title']).lower().strip()
        if t in found and found[t] is None:
            found[t] = i + 1
    
    print("Ranks of key titles:")
    for k, v in found.items():
        print(f"  {k}: Rank {v if v else 'Not in Top 1000'}")

run_experiment('A', jd)
run_experiment('B', jd)
run_experiment('C', jd)
