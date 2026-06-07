import json
import pandas as pd
import numpy as np
import copy
import re
from engine import RankingEngine

engine = RankingEngine()

jd = {
    'family': 'Sales Manager',
    'keywords': ['sales', 'crm', 'b2b', 'revenue', 'quota', 'pipeline', 'account', 'business development'],
    'title_terms': ["Sales Manager", "Account Executive", "Business Development Manager", "Sales Director", "VP of Sales", "Revenue Manager"],
    'req_skills': ["sales", "b2b", "crm", "salesforce", "hubspot", "quota", "pipeline", "outbound", "inbound", "lead generation", "negotiation", "closing", "prospecting", "account management"]
}

# Run Baseline
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

total_var = sum(var_metrics.values())
print("\n1. Percentage of final score variance (Top 100):")
for col, v in var_metrics.items():
    print(f"  {col}: {(v/total_var)*100:.2f}%")

# Q2: Accountant at Rank #1
acc_id = results[0]['candidate_id']
acc_row = df_feat[df_feat['candidate_id'] == acc_id].iloc[0]

# Which tokens matched?
s_text = acc_row['skills_text']
d_text = acc_row['desc_text']
t_text = acc_row['current_title']

sk_hits = [k for k in jd['req_skills'] if k in s_text]
c_hits = [k for k in jd['keywords'] if k in d_text]
sem_hits = [k for k in jd['keywords'] if k in (s_text + " " + d_text)]

# Which dictionary entries fired?
cand_t_fams = [(fam, [w for w in terms if w in t_text]) for fam, terms in engine.config['role_families'].items()]
cand_s_fams = [(fam, [w for w in terms if w in s_text]) for fam, terms in engine.config['skill_families'].items()]
cand_c_fams = [(fam, [w for w in terms if w in d_text]) for fam, terms in engine.config['skill_families'].items()]

print(f"\n2. For the Accountant ({acc_id}) at Rank #1:")
print(f"  Raw Skill Affinity: {acc_row['skill_affinity']} -> Contrib: {acc_row['skill_affinity'] * engine.config['weights']['skill_affinity']}")
print(f"  Raw Career Affinity: {acc_row['career_affinity']} -> Contrib: {acc_row['career_affinity'] * engine.config['weights']['career_affinity']}")
print(f"  Exact Skill Tokens Matched: {sk_hits}")
print(f"  Exact Career Tokens Matched: {c_hits}")
print(f"  Dictionary role title matches: {[(f, hits) for f, hits in cand_t_fams if hits]}")
print(f"  Dictionary skill matches (s_text): {[(f, hits) for f, hits in cand_s_fams if hits]}")
print(f"  Dictionary career matches (d_text): {[(f, hits) for f, hits in cand_c_fams if hits]}")

# Q3: Title Affinity Forced to Zero
print("\n3. If Title Affinity is forced to zero:")
df_no_title = df_feat.copy()
df_no_title['title_affinity'] = 0.0
ranked_no_title = engine._rank_features(df_no_title)
print("  Top 5 candidates with 0 Title Affinity:")
for i, (_, row) in enumerate(ranked_no_title.head(5).iterrows()):
    print(f"    {i+1}. {row['candidate_id']} | {row['current_title']} | Score: {row['final_score']:.3f}")

# Q4: Quality Score Removed
df_no_qual = df_feat.copy()
df_no_qual['quality_score'] = 0.0
ranked_no_qual = engine._rank_features(df_no_qual)
rank_acc_no_qual = np.where(ranked_no_qual['candidate_id'] == acc_id)[0][0] + 1
print(f"\n4. If Quality Score is removed: Accountant rank becomes #{rank_acc_no_qual}")

# Q5: Skill Affinity Removed
df_no_sk = df_feat.copy()
df_no_sk['skill_affinity'] = 0.0
ranked_no_sk = engine._rank_features(df_no_sk)
rank_acc_no_sk = np.where(ranked_no_sk['candidate_id'] == acc_id)[0][0] + 1
print(f"5. If Skill Affinity is removed: Accountant rank becomes #{rank_acc_no_sk}")

# Q6: Career Affinity Removed
df_no_car = df_feat.copy()
df_no_car['career_affinity'] = 0.0
ranked_no_car = engine._rank_features(df_no_car)
rank_acc_no_car = np.where(ranked_no_car['candidate_id'] == acc_id)[0][0] + 1
print(f"6. If Career Affinity is removed: Accountant rank becomes #{rank_acc_no_car}")


print("\n=== PART 2: REQUIRED EXPERIMENTS ===")

def has_token(token, text):
    pattern = r'\b' + re.escape(token) + r'\b'
    return re.search(pattern, text) is not None

class ExperimentEngine(RankingEngine):
    def __init__(self, mode='A'):
        super().__init__()
        self.mode = mode
        if mode in ['B', 'C']:
            # Dictionary cleanup
            for f in ['manager', 'executive', 'account', 'marketing']:
                if f in self.config['role_families']['Sales Manager']:
                    self.config['role_families']['Sales Manager'].remove(f)

    def _extract_features(self, jd_data):
        if self.mode in ['A', 'C']:
            # Token aware matching
            feat = self.df[['candidate_id', 'current_title', 'quality_score', 'skills_text', 'skills', 'desc_text']].copy()
            jd_fam = jd_data['family']
            
            def ext_features_token(row):
                s_text = row['skills_text']
                d_text = row['desc_text']
                t_text = row['current_title']
                full = s_text + " " + d_text
                
                t_hits = sum(1 for w in jd_data['title_terms'] if has_token(w, t_text))
                taff = min(t_hits / 2.0, 1.0)
                
                sk_hits = sum(1 for k in jd_data['req_skills'] if has_token(k, s_text))
                saff = sk_hits / max(len(jd_data['req_skills']), 1)
                
                c_hits = sum(1 for k in jd_data['keywords'] if has_token(k, d_text))
                caff = c_hits / max(len(jd_data['keywords']), 1)
                
                hits = sum(1 for k in jd_data['keywords'] if has_token(k, full))
                sem = hits / max(len(jd_data['keywords']), 1)
                bm25 = sem * 0.8
                
                cand_t_fam = max([(fam, sum(1 for w in terms if has_token(w, t_text))) for fam, terms in self.config['role_families'].items()], key=lambda x: x[1])
                cand_s_fam = max([(fam, sum(1 for k in terms if has_token(k, s_text))) for fam, terms in self.config['skill_families'].items()], key=lambda x: x[1])
                cand_c_fam = max([(fam, sum(1 for k in terms if has_token(k, d_text))) for fam, terms in self.config['skill_families'].items()], key=lambda x: x[1])
                
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
    eng = ExperimentEngine(mode=mode)
    res = eng.run_pipeline(jd_base)
    
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
    
    # Ranks
    titles = ['sales manager', 'sales executive', 'account executive', 'business development manager', 'revenue operations manager', 'customer success manager']
    found = {t: None for t in titles}
    for i, c in enumerate(res):
        t = str(c['title']).lower().strip()
        if t in found and found[t] is None:
            found[t] = i + 1
    
    print("Ranks of key titles:")
    for k, v in found.items():
        print(f"  {k}: Rank {v if v else 'Not in Top 100'}")

run_experiment('A', jd)
run_experiment('B', jd)
run_experiment('C', jd)
