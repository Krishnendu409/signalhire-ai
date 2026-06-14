# Phase 1: Eligibility Audit

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
| **Total Candidates Evaluated** | 100000 |
| Removed by Experience | 33877 |
| Removed by Budget | 2250 |
| Removed by Work Mode | 50076 |
| Removed by Certification | 87374 |
| **Total Candidates Passed** | 4065 |

## Conclusion
The hard eligibility layer successfully prunes candidates based on recruiter non-negotiables before BM25/Semantic scoring occurs, improving processing efficiency and candidate relevance.
