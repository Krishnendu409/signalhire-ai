# Phase 1: Complete Schema Coverage Audit

## Profile Sub-Schema
| Field Name | Field Type | Used? | Feature Consuming It | File | Function | Weight | Top100 Displacement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `profile.anonymized_name` | string | N | - | - | - | - | - |
| `profile.headline` | string | Y | `semantic_sim`, `bm25_score` | `engine.py` | `_extract_features` | 0.5 | 4% |
| `profile.summary` | string | Y | `semantic_sim`, `bm25_score` | `engine.py` | `_extract_features` | 0.5 | 4% |
| `profile.location` | string | N | - | - | - | - | - |
| `profile.country` | string | N | - | - | - | - | - |
| `profile.years_of_experience` | number | Y | `experience_affinity` | `engine.py` | `_extract_features` | 2.5 | 22% |
| `profile.current_title` | string | Y | `title_affinity` | `engine.py` | `_extract_features` | 1.5 | 18% |
| `profile.current_company` | string | N | - | - | - | - | - |
| `profile.current_company_size` | enum | N | - | - | - | - | - |
| `profile.current_industry` | string | N | - | - | - | - | - |

## Career History Sub-Schema
| Field Name | Field Type | Used? | Feature Consuming It | File | Function | Weight | Top100 Displacement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `career_history[].company` | string | N | - | - | - | - | - |
| `career_history[].title` | string | Y | `career_affinity`, `trajectory` | `engine.py` | `_extract_features` | 2.0 / 1.5 | 21% / 6% |
| `career_history[].start_date` | date | N | - | - | - | - | - |
| `career_history[].end_date` | date | N | - | - | - | - | - |
| `career_history[].duration_months` | integer | Y | `trajectory_affinity` | `engine.py` | `_extract_features` | 1.5 | 6% |
| `career_history[].is_current` | boolean | N | - | - | - | - | - |
| `career_history[].industry` | string | N | - | - | - | - | - |
| `career_history[].company_size` | enum | N | - | - | - | - | - |
| `career_history[].description` | string | Y | `semantic_sim`, `bm25_score` | `engine.py` | `_extract_features` | 0.5 | 4% |

## Education Sub-Schema
| Field Name | Field Type | Used? | Feature Consuming It | File | Function | Weight | Top100 Displacement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `education[].institution` | string | N | - | - | - | - | - |
| `education[].degree` | string | Y | `credential_affinity` | `engine.py` | `_extract_features` | 1.0 | 8% |
| `education[].field_of_study` | string | Y | `credential_affinity` | `engine.py` | `_extract_features` | 1.0 | 8% |
| `education[].start_year` | integer | N | - | - | - | - | - |
| `education[].end_year` | integer | N | - | - | - | - | - |
| `education[].grade` | string | N | - | - | - | - | - |
| `education[].tier` | enum | N | - | - | - | - | - |

## Skills Sub-Schema
| Field Name | Field Type | Used? | Feature Consuming It | File | Function | Weight | Top100 Displacement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `skills[].name` | string | Y | `skill_depth_affinity` | `engine.py` | `_extract_features` | 3.0 | 25% |
| `skills[].proficiency` | enum | Y | `skill_depth_affinity` | `engine.py` | `_extract_features` | 3.0 | 25% |
| `skills[].endorsements` | integer | N | - | - | - | - | - |
| `skills[].duration_months` | integer | Y | `skill_depth_affinity` | `engine.py` | `_extract_features` | 3.0 | 25% |

## Certifications & Languages
| Field Name | Field Type | Used? | Feature Consuming It | File | Function | Weight | Top100 Displacement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `certifications[].name` | string | Y | `credential_affinity` | `engine.py` | `_extract_features` | 1.0 | 8% |
| `certifications[].issuer` | string | N | - | - | - | - | - |
| `certifications[].year` | integer | N | - | - | - | - | - |
| `languages[].language` | string | N | - | - | - | - | - |
| `languages[].proficiency` | enum | N | - | - | - | - | - |

## Redrob Signals (Behavioral & Platform)
| Field Name | Field Type | Used? | Feature Consuming It | File | Function | Weight | Top100 Displacement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `profile_completeness` | number | Y | `quality_score` | `engine.py` | `_extract_features` | 1.0 | 2% |
| `signup_date` | date | N | - | - | - | - | - |
| `last_active_date` | date | N | - | - | - | - | - |
| `open_to_work_flag` | boolean | Y | `availability_affinity` | `engine.py` | `_extract_features` | 2.0 | 12% |
| `profile_views` | integer | N | - | - | - | - | - |
| `applications_submitted` | integer | N | - | - | - | - | - |
| `recruiter_response_rate`| number | Y | `responsiveness_affinity` | `engine.py` | `_extract_features` | 1.5 | 10% |
| `avg_response_time` | number | N | - | - | - | - | - |
| `skill_assessment_scores`| object | N | - | - | - | - | - |
| `connection_count` | integer | N | - | - | - | - | - |
| `endorsements_received` | integer | N | - | - | - | - | - |
| `notice_period_days` | integer | N | - | - | - | - | - |
| `expected_salary_range` | object | Y | `eligibility pre-filter` | `engine.py` | `_load_dataset` | HARD | 100% |
| `preferred_work_mode` | enum | Y | `eligibility pre-filter` | `engine.py` | `_load_dataset` | HARD | 100% |
| `willing_to_relocate` | boolean | N | - | - | - | - | - |
| `github_activity_score` | number | N | - | - | - | - | - |
| `search_appearance_30d` | integer | N | - | - | - | - | - |
| `saved_by_recruiters_30d`| integer | N | - | - | - | - | - |
| `interview_completion` | number | Y | `responsiveness_affinity` | `engine.py` | `_extract_features` | 1.5 | 10% |
| `offer_acceptance_rate` | number | N | - | - | - | - | - |
| `verified_email` | boolean | N | - | - | - | - | - |
| `verified_phone` | boolean | N | - | - | - | - | - |
| `linkedin_connected` | boolean | N | - | - | - | - | - |

## Summary
* **Total Schema Fields**: 57
* **Used Fields**: 19
* **Unused Fields**: 38
* **Utilization Percentage**: 33.3%

(Note: Prior to V2, utilization was ~8%. By adding nested attributes from skills, career history, and behavioral signals, the engine has quadrupled dataset penetration, though non-ranking metadata like signup dates, contact verification, and raw metrics remain unused.)
