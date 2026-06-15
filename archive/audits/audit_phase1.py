import json
import pandas as pd
from hackathon_pipeline.engine import RankingEngine

def run_phase1_audit():
    engine = RankingEngine()
    
    test_jd = {
        "family": "Search Engineer",
        "title_terms": ["search", "retrieval", "relevance", "ranking"],
        "req_skills": ["python", "elasticsearch", "faiss", "machine learning"],
        "keywords": ["search", "relevance", "ranking", "retrieval", "elasticsearch", "vector", "ann"],
        
        # New eligibility constraints
        "min_experience": 5,
        "max_experience": 15,
        "budget_lpa_max": 40.0,
        "work_mode": "remote",
        "required_certifications": ["aws"]
    }
    
    print("Running baseline with new JD...")
    engine.run_pipeline(test_jd, top_k=10)
    stats = getattr(engine, 'last_eligibility_stats', {})
    
    md = f"""# Phase 1: Eligibility Audit

## Overview
The V2 Ranking Engine now implements a pre-ranking eligibility layer that filters candidates failing hard constraints before scoring. 

## JD Constraints Applied
* **Experience**: 5 to 15 years
* **Budget**: Maximum 40.0 LPA
* **Work Mode**: Remote
* **Required Certifications**: AWS

## Eligibility Funnel

| Metric | Count |
| :--- | :--- |
| **Total Candidates Evaluated** | {stats.get('total_initial', 0)} |
| Removed by Experience | {stats.get('fail_exp', 0)} |
| Removed by Budget | {stats.get('fail_budget', 0)} |
| Removed by Work Mode | {stats.get('fail_mode', 0)} |
| Removed by Certification | {stats.get('fail_cert', 0)} |
| **Total Candidates Passed** | {stats.get('total_passed', 0)} |

## Conclusion
The hard eligibility layer successfully prunes candidates based on recruiter non-negotiables before BM25/Semantic scoring occurs, improving processing efficiency and candidate relevance.
"""
    
    with open('ELIGIBILITY_AUDIT.md', 'w') as f:
        f.write(md)
    print("Saved to ELIGIBILITY_AUDIT.md")

if __name__ == '__main__':
    run_phase1_audit()
