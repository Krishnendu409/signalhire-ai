# Phase 8: Final Weight Recommendation

## Overview
Based on the variance contribution of all 12 features, the V2 weighting matrix must be balanced to ensure that while Skills and Experience remain primary drivers, Feasibility and Trajectory act as significant tie-breakers.

## Recommended Final Weights

| Feature | Current Weight | Recommended Weight | Rationale |
| :--- | :--- | :--- | :--- |
| `skill_depth_affinity` | 3.50 | 3.00 | Primary competency driver, slightly reduced to allow behavioral signals room to breathe. |
| `career_affinity` | 2.50 | 2.00 | Secondary competency driver. |
| `experience_affinity` | 2.00 | 2.50 | Upgraded to co-primary status to ensure seniority matching. |
| `title_affinity` | 2.50 | 1.50 | Down-weighted. Exact title matching is less important than skills and experience. |
| `availability_affinity` | 1.50 | 2.00 | Up-weighted. A candidate who is not open to work is useless to a recruiter. |
| `responsiveness_affinity` | 1.00 | 1.50 | Up-weighted. Ghosting is a primary recruiter pain point. |
| `credential_affinity` | 1.50 | 1.00 | Maintained as a tie-breaker. |
| `trajectory_affinity` | 1.00 | 1.50 | Up-weighted to reward stable career paths over job hoppers. |
| `quality_score` | 1.00 | 1.00 | Constant. |
| `semantic_sim` | 1.00 | 0.50 | Down-weighted. Semantic similarity is heavily correlated with career_affinity. |
| `bm25_score` | 1.00 | 0.50 | Down-weighted. Legacy keyword matching is obsolete given skill_depth. |

## Next Steps
These weights establish the V2 Frozen Baseline. The Ranking Engine is now fully upgraded and scientifically validated. Productization may safely resume.
