import os

# 1. Update feature_extractor.py
fe_path = 'feature_extractor.py'
with open(fe_path, 'r', encoding='utf-8') as f:
    fe_code = f.read()

# Add domain authenticity logic right before "17. Profile Completeness"
auth_logic = """
        # 16c. Domain Authenticity Score (NEW)
        eng_titles = {'engineer', 'developer', 'scientist', 'architect', 'researcher', 'data'}
        trap_titles = {'manager', 'support', 'designer', 'accountant', 'hr', 'sales', 'writer', 'analyst'}
        eng_keywords = {'code', 'system', 'build', 'architecture', 'deploy', 'model', 'algorithm', 'pipeline', 'software', 'backend', 'api'}
        
        auth_score = 0.0
        c_title_lower = current_title.lower()
        if any(e in c_title_lower for e in eng_titles):
            auth_score += 1.0
        elif any(t in c_title_lower for t in trap_titles) and 'engineering manager' not in c_title_lower:
            auth_score -= 1.0
            
        desc_hits = sum(1 for k in eng_keywords if k in full_text)
        if desc_hits >= 3:
            auth_score += 1.0
        elif desc_hits == 0:
            auth_score -= 1.0
            
        tech_skills = {'python', 'java', 'aws', 'sql', 'machine learning', 'react', 'node.js', 'docker', 'kubernetes', 'faiss', 'pinecone'}
        non_tech = {'excel', 'figma', 'sales', 'accounting', 'content writing', 'agile', 'scrum', 'marketing', 'tally'}
        
        t_count = sum(1 for s in skills_list if (s.get('name', '') or '').lower() in tech_skills)
        nt_count = sum(1 for s in skills_list if (s.get('name', '') or '').lower() in non_tech)
        
        if t_count > nt_count:
            auth_score += 1.0
        elif nt_count > t_count:
            auth_score -= 1.0
            
        features.at[idx, 'domain_authenticity_score'] = max(-3.0, min(3.0, auth_score))

        # =============================================
"""

fe_code = fe_code.replace("        # =============================================\n        # NEW: Previously Unused redrob_signals\n        # =============================================", auth_logic + "        # NEW: Previously Unused redrob_signals\n        # =============================================")

# Add to FEATURE_COLS
new_feature_cols = """FEATURE_COLS = [
    'semantic_sim', 'bm25_score',
    'retrieval_experience_score', 'ranking_experience_score', 'embedding_experience_score',
    'vector_db_score', 'evaluation_framework_score', 'production_ml_score',
    'hireability_score', 'career_consistency_score', 'timeline_consistency_score',
    'recruiter_interest_score', 'startup_readiness_score', 'leadership_score',
    'product_ownership_score', 'synthetic_risk_score', 'role_progression_score',
    'jd_disqualifier_penalty', 'keyword_trap_risk', 'domain_authenticity_score', 'github_activity_score',
    'profile_completeness', 'avg_skill_assessment', 'trust_score'
]"""

fe_code = fe_code.replace("""FEATURE_COLS = [
    'semantic_sim', 'bm25_score',
    'retrieval_experience_score', 'ranking_experience_score', 'embedding_experience_score',
    'vector_db_score', 'evaluation_framework_score', 'production_ml_score',
    'hireability_score', 'career_consistency_score', 'timeline_consistency_score',
    'recruiter_interest_score', 'startup_readiness_score', 'leadership_score',
    'product_ownership_score', 'synthetic_risk_score', 'role_progression_score',
    'jd_disqualifier_penalty', 'keyword_trap_risk', 'github_activity_score',
    'profile_completeness', 'avg_skill_assessment', 'trust_score'
]""", new_feature_cols)

with open(fe_path, 'w', encoding='utf-8') as f:
    f.write(fe_code)

# 2. Update train_lightgbm.py
tl_path = 'train_lightgbm.py'
with open(tl_path, 'r', encoding='utf-8') as f:
    tl_code = f.read()

# Replace generate_training_data content
old_math = """        # Core JD alignment (highest weight)
        core = (
            row['retrieval_experience_score'] * 2.5 +
            row['ranking_experience_score'] * 2.5 +
            row['embedding_experience_score'] * 2.0 +
            row['vector_db_score'] * 2.0 +
            row['evaluation_framework_score'] * 2.0 +
            row['production_ml_score'] * 1.5
        )

        # Soft skills & reliability
        soft = (
            row['startup_readiness_score'] * 1.0 +
            row['leadership_score'] * 1.0 +
            row['product_ownership_score'] * 1.0 +
            row['hireability_score'] * 1.5 +
            row['recruiter_interest_score'] * 0.5 +
            row['role_progression_score'] * 0.8
        )

        # Trust & profile quality
        trust = (
            row['profile_completeness'] * 1.0 +
            row['avg_skill_assessment'] * 1.5 +
            row['trust_score'] * 0.5 +
            row['github_activity_score'] * 1.0
        )

        # Consistency & penalties (can go negative)
        penalties = (
            row['career_consistency_score'] * 2.0 +
            row['timeline_consistency_score'] * 1.5 +
            row['jd_disqualifier_penalty'] * 1.0 -
            row['synthetic_risk_score'] * 0.3 -
            row.get('keyword_trap_risk', 0.0) * 1.5
        )

        # Query-dependent (simulated)
        query = row['semantic_sim'] * 3.0 + row['bm25_score'] * 1.5

        final_score = core + soft + trust + penalties + query"""

new_math = """        # Core JD alignment
        core = (
            row['retrieval_experience_score'] * 2.5 +
            row['ranking_experience_score'] * 2.5 +
            row['embedding_experience_score'] * 2.0 +
            row['vector_db_score'] * 1.0 +
            row['evaluation_framework_score'] * 2.0 +
            row['production_ml_score'] * 1.5
        )

        # Domain Authenticity
        domain = (row['domain_authenticity_score'] * 1.5)

        # Soft skills & reliability
        soft = (
            row['startup_readiness_score'] * 1.0 +
            row['leadership_score'] * 1.0 +
            row['product_ownership_score'] * 1.0 +
            row['hireability_score'] * 1.5 +
            row['recruiter_interest_score'] * 0.5 +
            row['role_progression_score'] * 0.8
        )

        # Trust & profile quality
        trust = (
            row['profile_completeness'] * 1.0 +
            row['avg_skill_assessment'] * 1.5 +
            row['trust_score'] * 0.5 +
            row['github_activity_score'] * 1.0
        )

        # Consistency & penalties (can go negative)
        penalties = (
            row['career_consistency_score'] * 2.0 +
            row['timeline_consistency_score'] * 1.5 +
            row['jd_disqualifier_penalty'] * 1.0 -
            row['synthetic_risk_score'] * 0.3 -
            row.get('keyword_trap_risk', 0.0) * 3.0
        )

        # Query-dependent (simulated)
        query = row['semantic_sim'] * 3.0 + row['bm25_score'] * 1.5

        final_score = core + domain + soft + trust + penalties + query"""

tl_code = tl_code.replace(old_math, new_math)

# Replace group logic
old_group = """    # Single group (all candidates ranked against one query)
    group = [len(X)]"""

new_group = """    # Chunk groups to avoid LightGBM maximum group size (10000)
    import math
    max_group_size = 5000
    num_full_groups = len(X) // max_group_size
    remainder = len(X) % max_group_size
    group = [max_group_size] * num_full_groups
    if remainder > 0:
        group.append(remainder)"""

tl_code = tl_code.replace(old_group, new_group)

# Also update num_samples in generate_training_data default to 20000
tl_code = tl_code.replace("def generate_training_data(input_path, num_samples=10000):", "def generate_training_data(input_path, num_samples=20000):")

with open(tl_path, 'w', encoding='utf-8') as f:
    f.write(tl_code)

print("Patch applied to feature_extractor.py and train_lightgbm.py.")
