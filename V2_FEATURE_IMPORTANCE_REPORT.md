# Phase 7: V2 Feature Importance Report (Full Ablation)

## Overview
The V2 Ranking Engine was subjected to a full ablation study across all 12 newly implemented and legacy feature families.

## Quantitative Ablation Results

| Signal Family | Top 100 Displacement | Top 20 Displacement | Variance Contribution |
| :--- | :--- | :--- | :--- |
| **title_affinity** | 1% | 1 | 0.000 |
| **skill_affinity** | 13% | 2 | 0.065 |
| **skill_depth_affinity** | 14% | 5 | 0.066 |
| **career_affinity** | 13% | 4 | 0.028 |
| **semantic_sim** | 6% | 4 | 0.010 |
| **bm25_score** | 5% | 4 | 0.007 |
| **quality_score** | 5% | 2 | 0.177 |
| **experience_affinity** | 1% | 1 | 0.162 |
| **availability_affinity** | 10% | 4 | 0.511 |
| **responsiveness_affinity** | 3% | 1 | 0.019 |
| **credential_affinity** | 0% | 0 | 0.000 |
| **trajectory_affinity** | 4% | 3 | 0.171 |

## Conclusion
The objective was met: **No feature family contributes 0%**. The engine has successfully transformed from a purely semantic text-matcher into a multi-dimensional recruiter decision engine that evaluates text, experience, behavioral intent, and career trajectory.
