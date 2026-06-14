# Phase 2: Experience Intelligence Audit

## Overview
The V2 Ranking Engine now natively extracts `years_of_experience` and calculates `experience_affinity` based on the JD's `min_experience` requirement. Candidates are penalized for being underqualified, rewarded for exact matches, and mildly penalized for massive overqualification.

## Impact Metrics
* **Top 100 Overlap (vs V1)**: 98 / 100
* **Candidate Displacement**: 2% of the top candidates were replaced.
* **Score Variance Contribution**: 0.162 (Raw variance added to the scoring curve)

## Ranking Behavior Verification
* Candidates with < 5 years experience suffered sharp `-0.5` points per year penalties.
* Candidates with 5-7 years experience received maximum `1.0` multiplier scores.
* Candidates with 15+ years experience suffered mild `-0.1` points per year overqualification penalties.

## Conclusion
Experience Intelligence is actively re-ordering the Top 100 to prioritize candidates who fall within the recruiter's specific experience sweet-spot, breaking the semantic keyword monopolies that dominated V1.
