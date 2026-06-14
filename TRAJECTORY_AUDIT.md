# Phase 6: Career Trajectory Audit

## Overview
The V2 Ranking Engine now evaluates the `career_history` array to extract promotion velocity and job stability.

## Impact Metrics
* **Top 100 Overlap**: 96 / 100
* **Candidate Displacement**: 4% 
* **Score Variance Contribution**: 0.171

## Ranking Behavior Verification
* Candidates showing a logical progression to "Senior" or "Lead" roles gained a permanent score boost.
* Serial job-hoppers (multiple stints < 8 months) incurred scaling penalties, resulting in displacement out of the Top 100 for otherwise highly-skilled candidates.

## Conclusion
The Trajectory Layer adds critical historical context to semantic skills, differentiating between candidates who casually dabble in a skill versus those who have built stable, senior careers around it.
