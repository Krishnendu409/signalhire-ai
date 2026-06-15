import json
import pandas as pd
import numpy as np
import os
import time

class RankingEngine:
    def __init__(self):
        print("Initializing Deterministic Ranking Engine v1.0...")
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

    def _prepare_df(self, candidates: list[dict]):
        records = []
        raw_data = {}
        for c in candidates:
            # Flatten parsed_data with candidate_id
            record = c.get('parsed_data', {}).copy()
            cid = str(c.get('id', ''))
            record['candidate_id'] = cid
            records.append(record)
            raw_data[cid] = record

        df = pd.DataFrame(records)
        if df.empty:
            return df, raw_data

        # Safely extract current title
        def get_title(row):
            t = row.get('current_title')
            if isinstance(t, str) and t.strip():
                return t.lower()
            ch = row.get('career_history', [])
            if isinstance(ch, list) and len(ch) > 0 and isinstance(ch[0], dict):
                return ch[0].get('title', '').lower()
            return ''
        
        df['current_title'] = df.apply(get_title, axis=1)

        def get_skills(row):
            s_list = row.get('skills', [])
            if not isinstance(s_list, list): return ""
            return " ".join([s.get('name', '').lower() for s in s_list if isinstance(s, dict)])
        
        if 'skills' in df.columns:
            df['skills_text'] = df.apply(get_skills, axis=1)
        else:
            df['skills_text'] = ''

        def get_desc(row):
            ch = row.get('career_history', [])
            if not isinstance(ch, list): return ""
            return " ".join([c.get('description', '').lower() for c in ch if isinstance(c, dict)])
        
        if 'career_history' in df.columns:
            df['desc_text'] = df.apply(get_desc, axis=1)
        else:
            df['desc_text'] = ''

        def calc_quality(c):
            s = c.get('redrob_signals', {})
            if not isinstance(s, dict): return 0.0
            q = 0.0
            q += (s.get('profile_completeness_score', 50) / 100.0)
            q += min((s.get('github_activity_score', 0) / 100.0), 1.0)
            if s.get('verified_email'): q += 0.5
            if s.get('linkedin_connected'): q += 0.5
            return q
            
        if 'redrob_signals' in df.columns:
            df['quality_score'] = df.apply(calc_quality, axis=1)
        else:
            df['quality_score'] = 0.5

        return df, raw_data

    def _extract_features(self, df, jd_data):
        import re
        feat = df[['candidate_id', 'current_title', 'quality_score', 'skills_text', 'desc_text']].copy()
        jd_fam = jd_data.get('family', 'Unknown')
        title_terms = jd_data.get('title_terms', [])
        if not title_terms and 'title' in jd_data:
            title_terms = [jd_data['title']] + jd_data['title'].split()
        req_skills = jd_data.get('req_skills', [])
        if not req_skills and 'required_hard_skills' in jd_data:
            req_skills = jd_data['required_hard_skills']
        keywords = jd_data.get('keywords', [])
        if not keywords:
            keywords = jd_data.get('required_soft_skills', []) + jd_data.get('preferred_skills', [])
        
        t_text_series = feat['current_title'].fillna('')
        s_text_series = feat['skills_text'].fillna('')
        d_text_series = feat['desc_text'].fillna('')
        full_series = s_text_series + " " + d_text_series
        
        t_hits_series = pd.Series(0, index=feat.index)
        for w in title_terms:
            t_hits_series += t_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True, case=False).astype(int)
        feat['title_affinity'] = (t_hits_series / 2.0).clip(upper=1.0)
        
        sk_hits_series = pd.Series(0, index=feat.index)
        matched_sk_list = []
        missing_sk_list = []
        for idx in feat.index:
            s_txt = s_text_series[idx]
            m_s = [w for w in req_skills if re.search(r'\b' + re.escape(w.lower()) + r'\b', s_txt, re.IGNORECASE)]
            mi_s = [w for w in req_skills if w not in m_s]
            matched_sk_list.append(','.join(m_s))
            missing_sk_list.append(','.join(mi_s))
            
        for w in req_skills:
            sk_hits_series += s_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True, case=False).astype(int)
            
        feat['skill_affinity'] = sk_hits_series / max(len(req_skills), 1)
        feat['matched_skills'] = matched_sk_list
        feat['missing_skills'] = missing_sk_list
        
        c_hits_series = pd.Series(0, index=feat.index)
        for w in keywords:
            c_hits_series += d_text_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
        feat['career_affinity'] = c_hits_series / max(len(keywords), 1)
        
        sem_hits_series = pd.Series(0, index=feat.index)
        for w in keywords:
            sem_hits_series += full_series.str.contains(r'\b' + re.escape(w.lower()) + r'\b', regex=True).astype(int)
        feat['semantic_sim'] = sem_hits_series / max(len(keywords), 1)
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
        
        jd_fam_known = jd_fam in self.config['role_families']
        if jd_fam_known:
            feat['is_inconsistent'] = (feat['t_fam'] != jd_fam) & (feat['t_fam'] != 'Unknown') & (feat['s_fam'] != jd_fam) & (feat['s_fam'] != 'Unknown') & (feat['c_fam'] != jd_fam) & (feat['c_fam'] != 'Unknown')
            feat['is_partial'] = ~feat['is_consistent'] & ~feat['is_inconsistent']
        else:
            feat['is_inconsistent'] = False
            feat['is_partial'] = False
            
        is_sales = (jd_fam == 'Sales Manager')
        if is_sales:
            feat['is_trap'] = feat['current_title'].str.contains('engineer|developer|scientist|data')
        else:
            feat['is_trap'] = feat['current_title'].apply(lambda t: any(tr in t for tr in self.config['trap_titles']) and 'engineer' not in t)
        
        return feat


    def _apply_transferable_skills(self, jd_data, candidates_df):
        transfer_map = {
            "vue": "react",
            "angular": "react",
            "rabbitmq": "kafka",
            "pytorch": "tensorflow",
            "tensorflow": "pytorch",
            "c": "c++",
            "c++": "rust",
            "mysql": "postgresql",
        }
        
        req_skills = [s.lower() for s in jd_data.get('req_skills', [])]
        
        for idx, row in candidates_df.iterrows():
            cand_skills_text = row['skills_text']
            adjacent = []
            evidence = []
            bonus = 0.0
            
            for have, need in transfer_map.items():
                if need in req_skills and have in cand_skills_text and need not in cand_skills_text:
                    adjacent.append(have)
                    evidence.append(f"Candidate has {have.capitalize()} which transfers well to {need.capitalize()}")
                    bonus += 0.5
            
            if adjacent:
                candidates_df.at[idx, 'skill_affinity'] += bonus * (1.0 / max(len(req_skills), 1))
                candidates_df.at[idx, 'adaptation_risk'] = 'low' if bonus > 1.0 else 'medium'
                candidates_df.at[idx, 'adjacent_skills'] = ','.join(adjacent)
                candidates_df.at[idx, 'transferability_evidence'] = ';'.join(evidence)
            else:
                candidates_df.at[idx, 'adaptation_risk'] = 'high'
                candidates_df.at[idx, 'adjacent_skills'] = ''
                candidates_df.at[idx, 'transferability_evidence'] = ''
        return candidates_df

    def _rank_features(self, feat):
        feat['final_score'] = 0.0
        feat['penalties'] = np.where(feat['is_inconsistent'] | feat['is_partial'], self.config['weights']['consistency_penalty'], 0.0)
        
        for k in ['title_affinity', 'skill_affinity', 'career_affinity', 'semantic_sim', 'bm25_score', 'quality_score']:
            feat['final_score'] += feat[k] * self.config['weights'][k]
            
        feat['final_score'] += feat['penalties']
        
        total_max = sum(w for k, w in self.config['weights'].items() if k != 'consistency_penalty')
        feat['final_score'] = (feat['final_score'] / total_max) * 100.0
        feat['final_score'] = feat['final_score'].clip(lower=0.0)
            
        return feat.sort_values(by='final_score', ascending=False)

    def run_pipeline(self, jd_data, candidates: list[dict], top_k=100):
        """
        Executes the frozen ranking pipeline for a given JD.
        jd_data must have: 'family', 'keywords', 'title_terms', 'req_skills'
        """
        df, raw_data = self._prepare_df(candidates)
        if df.empty:
            return []

        feat_base = self._extract_features(df, jd_data)
        feat_base = self._apply_transferable_skills(jd_data, feat_base)
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
                'Penalties': float(row['penalties']),
                'adjacent_skills': row.get('adjacent_skills', '').split(',') if row.get('adjacent_skills', '') else [],
                'adaptation_risk': row.get('adaptation_risk', 'high'),
                'transferability_evidence': row.get('transferability_evidence', '').split(';') if row.get('transferability_evidence', '') else [],
                'matched_skills': row.get('matched_skills', '').split(',') if row.get('matched_skills', '') else [],
                'missing_skills': row.get('missing_skills', '').split(',') if row.get('missing_skills', '') else [],
                'explanation': f"Match score: {float(row['final_score']):.2f}. Missing skills: {row.get('missing_skills', 'None')}",

                'parsed_data': raw_data.get(row['candidate_id'], {}),
                'dimension_scores': {
                    'experience_affinity': {'score': float(row['career_affinity'] * 100)},
                    'skill_depth': {'score': float(row['skill_affinity'] * 100)}
                }
            })
            
        return output_records
