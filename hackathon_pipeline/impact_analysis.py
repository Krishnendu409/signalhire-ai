import json
import pandas as pd
from engine import RankingEngine
import copy

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

def get_current_outputs(jd_data):
    return engine.run_pipeline(jd_data, top_k=100)

class PatchedRankingEngine(RankingEngine):
    def _extract_features(self, jd_data):
        import re
        feat = self.df[['candidate_id', 'current_title', 'quality_score', 'skills_text', 'skills', 'desc_text']].copy()
        jd_fam = jd_data['family']
        
        t_text_series = feat['current_title'].fillna('')
        s_text_series = feat['skills_text'].fillna('')
        d_text_series = feat['desc_text'].fillna('')
        full_series = s_text_series + " " + d_text_series
        
        t_hits_series = pd.Series(0, index=feat.index)
        for w in jd_data['title_terms']:
            t_hits_series += t_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
        feat['title_affinity'] = (t_hits_series / 2.0).clip(upper=1.0)
        
        sk_hits_series = pd.Series(0, index=feat.index)
        for w in jd_data['req_skills']:
            sk_hits_series += s_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
        feat['skill_affinity'] = sk_hits_series / max(len(jd_data['req_skills']), 1)
        
        c_hits_series = pd.Series(0, index=feat.index)
        for w in jd_data['keywords']:
            c_hits_series += d_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
        feat['career_affinity'] = c_hits_series / max(len(jd_data['keywords']), 1)
        
        sem_hits_series = pd.Series(0, index=feat.index)
        for w in jd_data['keywords']:
            sem_hits_series += full_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
        feat['semantic_sim'] = sem_hits_series / max(len(jd_data['keywords']), 1)
        feat['bm25_score'] = feat['semantic_sim'] * 0.8
        
        t_fam_df = pd.DataFrame(index=feat.index)
        for fam, terms in self.config['role_families'].items():
            t_fam_df[fam] = 0
            for w in terms:
                t_fam_df[fam] += t_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
                
        s_fam_df = pd.DataFrame(index=feat.index)
        for fam, terms in self.config['skill_families'].items():
            s_fam_df[fam] = 0
            for w in terms:
                s_fam_df[fam] += s_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
                
        c_fam_df = pd.DataFrame(index=feat.index)
        # BUG FIX: changed from skill_families to role_families
        for fam, terms in self.config['role_families'].items():
            c_fam_df[fam] = 0
            for w in terms:
                c_fam_df[fam] += d_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
                
        feat['t_fam'] = t_fam_df.idxmax(axis=1)
        feat['t_fam'] = feat['t_fam'].where(t_fam_df.max(axis=1) > 0, 'Unknown')
        
        feat['s_fam'] = s_fam_df.idxmax(axis=1)
        feat['s_fam'] = feat['s_fam'].where(s_fam_df.max(axis=1) > 0, 'Unknown')
        
        feat['c_fam'] = c_fam_df.idxmax(axis=1)
        feat['c_fam'] = feat['c_fam'].where(c_fam_df.max(axis=1) > 0, 'Unknown')
        
        feat['is_consistent'] = (feat['t_fam'] == jd_fam) & (feat['s_fam'] == jd_fam) & (feat['c_fam'] == jd_fam)
        feat['is_inconsistent'] = (feat['t_fam'] != jd_fam) & (feat['t_fam'] != 'Unknown') & (feat['s_fam'] != jd_fam) & (feat['s_fam'] != 'Unknown') & (feat['c_fam'] != jd_fam) & (feat['c_fam'] != 'Unknown')
        feat['is_partial'] = ~feat['is_consistent'] & ~feat['is_inconsistent']
        
        is_sales = (jd_fam == 'Sales Manager')
        if is_sales:
            feat['is_trap'] = feat['current_title'].str.contains('engineer|developer|scientist|data')
        else:
            feat['is_trap'] = feat['current_title'].apply(lambda t: any(tr in t for tr in self.config['trap_titles']) and 'engineer' not in t)
        
        return feat

patched_engine = PatchedRankingEngine()
def get_patched_outputs(jd_data):
    return patched_engine.run_pipeline(jd_data, top_k=100)

results = []
for jd_name, jd_data in base_jds.items():
    cur = get_current_outputs(jd_data)
    pat = get_patched_outputs(jd_data)
    
    cur_ids100 = [c['candidate_id'] for c in cur]
    pat_ids100 = [c['candidate_id'] for c in pat]
    
    cur_ids20 = [c['candidate_id'] for c in cur[:20]]
    pat_ids20 = [c['candidate_id'] for c in pat[:20]]
    
    overlap100 = len(set(cur_ids100).intersection(set(pat_ids100)))
    overlap20 = len(set(cur_ids20).intersection(set(pat_ids20)))
    
    score_deltas = []
    for c_curr in cur:
        c_pat = next((x for x in pat if x['candidate_id'] == c_curr['candidate_id']), None)
        if c_pat:
            score_deltas.append(abs(c_curr['final_score'] - c_pat['final_score']))
            
    avg_delta = sum(score_deltas) / len(score_deltas) if score_deltas else 0
    max_delta = max(score_deltas) if score_deltas else 0
    
    results.append({
        'role': jd_name,
        'overlap100': overlap100,
        'overlap20': overlap20,
        'avg_delta': avg_delta,
        'max_delta': max_delta
    })

with open('impact_report.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Impact analysis complete.")
