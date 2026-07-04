import json
import pandas as pd
import numpy as np
import os
import time


def _resolve_dataset_path():
    """Portable dataset resolution (the previous hardcoded absolute path broke on any other
    machine and made the whole engine unloadable)."""
    candidates = [
        "../candidates.jsonl",
        "candidates.jsonl",
        "../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return "candidates.jsonl"


class RankingEngine:
    _df_cache = None
    def __init__(self, dataset_path=None):
        print("Initializing Frozen Ranking Engine v1.0...")
        self.config = {
            "weights": {
                'title_affinity': 2.50,
                'skill_affinity': 3.50,
                'career_affinity': 2.50,
                'semantic_sim': 1.00,
                'bm25_score': 1.00,
                'quality_score': 1.00,
                'consistency_penalty': -2.00
            },
            # NOTE: these three families are a FROZEN v1 contract — engine consistency is derived
            # via idxmax over every family, so adding a family here changes the scoring of the
            # others and breaks the regression baselines. The actual challenge "AI Engineer" JD is
            # ranked by the enhanced, separate pipeline in run_ranking.py, not by this frozen engine.
            "role_families": {
                'Search Engineer': ['search', 'retrieval', 'relevance', 'ranking', 'nlp', 'machine learning', 'ai', 'data scientist', 'ml'],
                'Frontend Engineer': ['frontend', 'ui', 'ux', 'client', 'web', 'javascript', 'react', 'angular', 'vue', 'front-end'],
                'Sales Manager': ['sales', 'revenue', 'business development', 'gtm', 'growth', 'customer success', 'account executive', 'territory']
            },
            "skill_families": {
                'Search Engineer': ['python', 'elasticsearch', 'faiss', 'machine learning', 'nlp', 'deep learning', 'pytorch', 'tensorflow', 'scikit-learn'],
                'Frontend Engineer': ['javascript', 'react', 'css', 'html', 'typescript', 'ui/ux', 'vue', 'angular', 'redux', 'next.js'],
                'Sales Manager': ['sales', 'crm', 'b2b', 'negotiation', 'leadership', 'pipeline', 'salesforce', 'marketing', 'quota']
            },
            "trap_titles": ['marketing', 'sales', 'hr', 'recruiter', 'manager', 'project manager', 'product manager', 'analyst', 'support', 'executive', 'director', 'accountant']
        }

        self.dataset_path = dataset_path or _resolve_dataset_path()
        self._load_dataset()

    def _load_dataset(self):
        if RankingEngine._df_cache is not None:
            self.df = RankingEngine._df_cache.copy()
            return
        records = []
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except:
                        pass

        self.df = pd.DataFrame(records)
        self.df['current_title'] = [ch[0].get('title', '').lower() if ch else '' for ch in self.df['career_history']]

        def get_skills(row):
            s_list = row.get('skills', []) or []
            return " ".join([s.get('name', '').lower() for s in s_list if isinstance(s, dict)])
        self.df['skills_text'] = self.df.apply(get_skills, axis=1)

        def get_desc(row):
            ch = row.get('career_history', [])
            return " ".join([c.get('description', '').lower() for c in ch if isinstance(c, dict)])
        self.df['desc_text'] = self.df.apply(get_desc, axis=1)

        def calc_quality(c):
            s = c.get('redrob_signals', {})
            q = 0.0
            q += (s.get('profile_completeness_score', 50) / 100.0)
            q += min((s.get('github_activity_score', 0) / 100.0), 1.0)
            if s.get('verified_email'): q += 0.5
            if s.get('linkedin_connected'): q += 0.5
            return q
        self.df['quality_score'] = self.df.apply(calc_quality, axis=1)

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
        for fam, terms in self.config['skill_families'].items():
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

    def _rank_features(self, feat):
        feat['final_score'] = 0.0
        feat['penalties'] = np.where(feat['is_inconsistent'] | feat['is_partial'], self.config['weights']['consistency_penalty'], 0.0)
        
        for k in ['title_affinity', 'skill_affinity', 'career_affinity', 'semantic_sim', 'bm25_score', 'quality_score']:
            feat['final_score'] += feat[k] * self.config['weights'][k]
            
        feat['final_score'] += feat['penalties']
            
        return feat.sort_values(by='final_score', ascending=False)

    def run_pipeline(self, jd_data, top_k=100):
        """
        Executes the frozen ranking pipeline for a given JD.
        jd_data must have: 'family', 'keywords', 'title_terms', 'req_skills'
        """
        start_time = time.time()
        
        feat_base = self._extract_features(jd_data)
        ranked = self._rank_features(feat_base)
        
        top100 = ranked.head(top_k)
        
        output_records = []
        for rank_idx, (_, row) in enumerate(top100.iterrows()):
            output_records.append({
                'rank': rank_idx + 1,
                'candidate_id': row['candidate_id'],
                'title': row['current_title'],
                'final_score': float(row['final_score']),
                'TitleAff_Contrib': float(row['title_affinity'] * self.config['weights']['title_affinity']),
                'SkillAff_Contrib': float(row['skill_affinity'] * self.config['weights']['skill_affinity']),
                'CareerAff_Contrib': float(row['career_affinity'] * self.config['weights']['career_affinity']),
                'SemSim_Contrib': float(row['semantic_sim'] * self.config['weights']['semantic_sim']),
                'BM25_Contrib': float(row['bm25_score'] * self.config['weights']['bm25_score']),
                'Quality_Contrib': float(row['quality_score'] * self.config['weights']['quality_score']),
                'Penalties': float(row['penalties'])
            })
            
        return output_records
