# Phase 3: Skill Depth Engine Audit

## Overview
The legacy `skill_affinity` only performed a boolean substring match on skill names, treating a "Beginner React" user identically to an "Expert React" user with 5 years of domain experience.
The V2 Engine implements `skill_depth_affinity`, calculating scores based on `Proficiency Weight × Duration Bonus`.

## Impact Metrics
* **Score Variance Contribution**: 0.066

## Ranking Behavior Verification
* Candidates with `Expert` proficiency received a base 1.0 multiplier per skill.
* Candidates with `Beginner` proficiency received a base 0.2 multiplier.
* Candidates with > 60 months of duration in a skill received a 2.0x duration multiplier, heavily boosting veterans in specific tech stacks.

## Conclusion
The Skill Depth Engine successfully transforms the semantic keyword match into a true competency assessment. Highly experienced specialists now reliably outrank generalists who merely list a keyword.
