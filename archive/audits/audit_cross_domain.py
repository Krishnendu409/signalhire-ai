import json
import pandas as pd
import numpy as np
import scipy.stats
from hackathon_pipeline.engine import RankingEngine

print("Loading engine...")
engine = RankingEngine()

roles = {
    "Data Scientist": {
        "family": "Unknown",
        "title_terms": ["data", "scientist", "machine learning", "ai", "analytics"],
        "req_skills": ["python", "r", "sql", "machine learning", "statistics", "pandas"],
        "keywords": ["data science", "modeling", "predictive", "algorithm", "analytics", "deep learning"]
    },
    "DevOps Engineer": {
        "family": "Unknown",
        "title_terms": ["devops", "sre", "reliability", "infrastructure", "platform"],
        "req_skills": ["aws", "docker", "kubernetes", "ci/cd", "terraform", "linux", "jenkins"],
        "keywords": ["infrastructure", "deployment", "automation", "cloud", "monitoring", "scalability"]
    },
    "Product Manager": {
        "family": "Unknown",
        "title_terms": ["product", "manager", "pm"],
        "req_skills": ["agile", "scrum", "roadmap", "strategy", "jira", "user research"],
        "keywords": ["product management", "stakeholder", "lifecycle", "requirements", "user stories", "metrics"]
    },
    "Project Manager": {
        "family": "Unknown",
        "title_terms": ["project", "manager", "pmp"],
        "req_skills": ["agile", "scrum", "pmp", "budgeting", "planning", "risk management"],
        "keywords": ["project management", "delivery", "milestones", "schedule", "stakeholders", "coordination"]
    },
    "QA Engineer": {
        "family": "Unknown",
        "title_terms": ["qa", "quality", "assurance", "tester", "sdet", "test"],
        "req_skills": ["selenium", "cypress", "testing", "automation", "java", "python", "pytest"],
        "keywords": ["quality assurance", "test cases", "manual testing", "automation testing", "bugs", "regression"]
    },
    "Security Engineer": {
        "family": "Unknown",
        "title_terms": ["security", "infosec", "cyber", "penetration", "soc"],
        "req_skills": ["security", "aws", "network", "firewall", "siem", "owasp", "cryptography"],
        "keywords": ["information security", "vulnerability", "incident response", "compliance", "threat", "risk"]
    },
    "Cloud Architect": {
        "family": "Unknown",
        "title_terms": ["cloud", "architect", "solutions"],
        "req_skills": ["aws", "azure", "gcp", "architecture", "microservices", "kubernetes", "networking"],
        "keywords": ["cloud computing", "design", "scalable", "infrastructure", "migration", "security"]
    },
    "Recruiter": {
        "family": "Unknown",
        "title_terms": ["recruiter", "talent", "acquisition", "hr", "sourcing"],
        "req_skills": ["sourcing", "screening", "linkedin", "ats", "interviewing", "negotiation"],
        "keywords": ["talent acquisition", "hiring", "recruitment", "candidates", "onboarding", "pipeline"]
    },
    "HR Manager": {
        "family": "Unknown",
        "title_terms": ["hr", "human", "resources", "manager", "people"],
        "req_skills": ["hris", "employee relations", "performance management", "benefits", "compliance", "training"],
        "keywords": ["human resources", "policies", "compensation", "culture", "development", "retention"]
    },
    "Marketing Manager": {
        "family": "Unknown",
        "title_terms": ["marketing", "manager", "growth", "campaign", "digital"],
        "req_skills": ["seo", "sem", "content", "social media", "analytics", "email marketing", "hubspot"],
        "keywords": ["digital marketing", "strategy", "campaigns", "branding", "lead generation", "b2b"]
    }
}

results = []

for role_name, jd_data in roles.items():
    print(f"Running for {role_name}...")
    feat_base = engine._extract_features(jd_data)
    ranked = engine._rank_features(feat_base)
    top100 = ranked.head(100)
    
    # Title distribution (top 3 titles)
    top_titles = top100['current_title'].value_counts().head(3).to_dict()
    
    # Honeypot penetration (assuming honeypot titles have specific flags? The user mentions "synthetic injections" are NOT allowed in Priority 1, meaning real honeypots might exist? Wait, honeypots are just candidates with trap titles.)
    # In engine.py, `is_trap` is calculated.
    honeypot_count = top100['is_trap'].sum()
    
    # Entropy of final scores in top 100
    scores = top100['final_score'].values
    prob = scores / (scores.sum() + 1e-9)
    entropy = scipy.stats.entropy(prob)
    
    # Top 20 Manual Review Placeholder - we will just save the top 5 for credibility assessment
    top5_titles = top100['current_title'].head(5).tolist()
    
    results.append({
        "Role": role_name,
        "Top Titles": str(top_titles),
        "Honeypots in Top 100": int(honeypot_count),
        "Score Entropy": float(entropy),
        "Top 5 Titles": str(top5_titles)
    })

df_res = pd.DataFrame(results)
print(df_res.to_markdown(index=False))
df_res.to_csv('cross_domain_results.csv', index=False)
print("Saved to cross_domain_results.csv")
