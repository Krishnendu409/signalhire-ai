import time
import os
import gc
try:
    import psutil
except ImportError:
    psutil = None
from hackathon_pipeline.engine import RankingEngine

def get_memory_mb():
    if psutil:
        return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    return 0.0

print("Initializing engine...")
engine = RankingEngine()
base_mem = get_memory_mb()
print(f"Base memory after init: {base_mem:.2f} MB")

jds = [
    {
        "family": "Search Engineer",
        "title_terms": ["search", "retrieval", "relevance", "ranking", "nlp", "machine learning", "ai", "data scientist", "ml"],
        "req_skills": ["python", "elasticsearch", "faiss", "machine learning", "nlp", "deep learning", "pytorch", "tensorflow", "scikit-learn"],
        "keywords": ["search", "vector", "embedding", "llm"],
        "min_experience": 5, "max_experience": 15, "budget_lpa_max": 999.0, "work_mode": "remote"
    },
    {
        "family": "Frontend Engineer",
        "title_terms": ["frontend", "ui", "ux", "client", "web", "javascript", "react", "angular", "vue", "front-end"],
        "req_skills": ["javascript", "react", "css", "html", "typescript", "ui/ux", "vue", "angular", "redux", "next.js"],
        "keywords": ["responsive", "component", "spa", "css3"],
        "min_experience": 3, "max_experience": 10, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    {
        "family": "Cloud Engineer",
        "title_terms": ["cloud", "devops", "infrastructure", "sre", "platform"],
        "req_skills": ["aws", "azure", "gcp", "kubernetes", "docker", "terraform", "ci/cd", "linux", "bash"],
        "keywords": ["deployment", "automation", "scaling", "monitoring"],
        "min_experience": 4, "max_experience": 12, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    {
        "family": "Data Analyst",
        "title_terms": ["data analyst", "business analyst", "bi", "reporting"],
        "req_skills": ["sql", "excel", "tableau", "powerbi", "python", "r", "statistics"],
        "keywords": ["dashboard", "metrics", "analytics", "visualization"],
        "min_experience": 2, "max_experience": 7, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    {
        "family": "HR Manager",
        "title_terms": ["hr", "human resources", "recruiter", "talent acquisition", "people"],
        "req_skills": ["sourcing", "interviewing", "onboarding", "employee relations", "workday", "greenhouse", "ats"],
        "keywords": ["hiring", "culture", "retention", "benefits"],
        "min_experience": 5, "max_experience": 15, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    {
        "family": "Content Writer",
        "title_terms": ["content", "writer", "copywriter", "editor", "technical writer"],
        "req_skills": ["writing", "editing", "seo", "blogging", "wordpress", "copywriting", "grammar"],
        "keywords": ["article", "publishing", "social media", "creative"],
        "min_experience": 2, "max_experience": 10, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    {
        "family": "Sales Manager",
        "title_terms": ["sales", "account executive", "business development", "ae", "sdr"],
        "req_skills": ["b2b", "crm", "salesforce", "negotiation", "prospecting", "cold calling", "closing"],
        "keywords": ["quota", "pipeline", "revenue", "outbound"],
        "min_experience": 3, "max_experience": 12, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    {
        "family": "Platform Engineer",
        "title_terms": ["platform", "infrastructure", "devops", "systems"],
        "req_skills": ["kubernetes", "golang", "python", "terraform", "aws", "docker", "ci/cd"],
        "keywords": ["scalability", "microservices", "automation", "reliability"],
        "min_experience": 4, "max_experience": 15, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    {
        "family": "Security Engineer",
        "title_terms": ["security", "infosec", "appsec", "cybersecurity"],
        "req_skills": ["penetration testing", "owasp", "python", "cryptography", "firewall", "siem"],
        "keywords": ["vulnerability", "threat", "compliance", "audit"],
        "min_experience": 3, "max_experience": 12, "budget_lpa_max": 999.0, "work_mode": "flexible"
    },
    {
        "family": "Product Manager",
        "title_terms": ["product manager", "pm", "owner"],
        "req_skills": ["agile", "scrum", "jira", "roadmap", "analytics", "user research"],
        "keywords": ["strategy", "vision", "stakeholder", "execution"],
        "min_experience": 4, "max_experience": 15, "budget_lpa_max": 999.0, "work_mode": "flexible"
    }
]

# Q1: Single JD runtime
print("\n--- Testing Single JD ---")
gc.collect()
t0 = time.time()
cands = engine.run_pipeline(jds[0], top_k=100)
t1 = time.time()
single_jd_time = t1 - t0
peak_mem_single = get_memory_mb()
print(f"Single JD Time: {single_jd_time:.2f} seconds")
print(f"Peak RAM after Single JD: {peak_mem_single:.2f} MB")

# Q2: 10 JDs runtime
print("\n--- Testing 10 JDs ---")
gc.collect()
t0 = time.time()
peak_mems = []
for i, jd in enumerate(jds):
    engine.run_pipeline(jd, top_k=100)
    peak_mems.append(get_memory_mb())
t1 = time.time()
ten_jd_time = t1 - t0
peak_mem_ten = max(peak_mems)
print(f"10 JDs Time: {ten_jd_time:.2f} seconds")
print(f"Peak RAM during 10 JDs: {peak_mem_ten:.2f} MB")

# Q4: Can process within limits
# 5 minutes = 300 seconds limit. If 10 JDs take < 300s, it passes.
print("\n--- Checking Competition Limits ---")
print("Competition limit for dataset scanning is 5 minutes (300 seconds).")
if ten_jd_time < 300:
    print(f"PASS: 10 JDs completed in {ten_jd_time:.2f}s, well within 300s.")
else:
    print(f"FAIL: 10 JDs completed in {ten_jd_time:.2f}s, exceeding 300s.")

# Q5: Remaining Ranking Failure Modes
# Let's verify honeypots for Search Engineer
print("\n--- Checking Honeypots ---")
cands = engine.run_pipeline(jds[0], top_k=100)
hps = sum(1 for c in cands[:20] if c.get('domain_authenticity', 0.0) < 0.2)
print(f"Search Engineer Top 20 Honeypots: {hps}")
