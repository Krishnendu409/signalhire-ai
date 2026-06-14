# Phase 6: Competition Readiness Review

## 1. If judges upload a completely unseen JD, why will the engine still work?

**Engineering Answer:**
The V2 engine no longer relies on hardcoded `role_families`. In V1, if a JD's title didn't exist in a static dictionary, the engine broke because it couldn't map the title to an archetype.
In V2, the engine operates as a generalized semantic and heuristic pipeline:
1. It extracts `req_skills` and maps them directly to the candidate's `skills` array, scaling by `proficiency` and `duration_months`.
2. It generates a single text block combining the JD's Title, Skills, and Keywords, and runs a dense vector `semantic_sim` search against the candidate's `career_history` text.
3. It filters candidates based on literal hardware constraints (`min_experience`, `budget_lpa_max`, `work_mode`).
If a judge uploads "Underwater Basket Weaver", the engine won't crash. It will simply look for candidates who have text semantically similar to "basket weaving" and who have the requisite years of experience and budget alignment.

## 2. If judges upload a role outside the 47 dataset titles, what exact fallback path executes?

**Engineering Answer:**
The candidate's `title_affinity` and `career_affinity` scores will simply return `0.0`. 
Because V2 uses a linear, additive feature weighting system (unlike a brittle decision tree that might crash if a feature is missing), the missing title match just means the candidate misses out on the 1.50 multiplier bonus.
The fallback is that the candidate's total score will be heavily reliant on:
- `skill_depth_affinity` (3.00 weight)
- `semantic_sim` (0.50 weight)
- `experience_affinity` (2.50 weight)
This is exactly how a human recruiter operates when sourcing for a niche role that has no standard title (e.g., looking at their specific skills and tenure rather than job title).

## 3. What percentage of schema fields are actively used?

**Engineering Answer:**
**33.3%** of the raw schema properties (19 out of 57 fields).
However, it utilizes **>85%** of the *meaningful* nested objects. It taps into `profile`, `career_history`, `education`, `skills`, `certifications`, and `redrob_signals`. 

## 4. What fields remain unused?

**Engineering Answer:**
The remaining unused fields fall into three categories:
1. **PII / Location**: `anonymized_name`, `location`, `country`. (Ignored intentionally to prevent bias).
2. **Metadata**: `signup_date`, `last_active_date`, `verified_email`, `verified_phone`, `linkedin_connected`. (Do not indicate candidate skill).
3. **Redrob Activity**: `profile_views`, `applications_submitted`, `connection_count`, `endorsements`, `search_appearance`. (These are popularity metrics, not competency metrics. Relying on them risks ranking "influencers" over "engineers").
4. **Prestige/Tiering**: `education.tier`, `education.grade`. (Ignored to prevent college-prestige bias).

## 5. What are the engine's biggest remaining weaknesses?

**Engineering Answer:**
1. **Linear Weighting Rigidity:** The weights are statically defined. A 2.50 weight for experience might be perfect for a Senior Cloud Engineer, but too strict for a Junior Marketing role. The engine cannot dynamically shift feature weights based on the *intent* of the JD.
2. **Semantic "Washing":** We are using a simple `SentenceTransformer` with mean-pooling on the JD text. This causes deep technical terms (e.g., "HNSW", "FAISS") to get washed out by generic terms (e.g., "Python", "Software").
3. **No Temporal Skill Decay:** A candidate who used React for 5 years between 2014-2019 scores identically to a candidate who used React for 5 years between 2020-2025.

## 6. What failure modes still exist?

**Engineering Answer:**
1. **Honeypot/Trap Candidates:** If a candidate stuffs their resume with "FAISS", "Pinecone", and "Kubernetes" but has the title "Graphic Designer" and 10 years of experience, `semantic_sim` and `skill_depth` will spike. Unless the `consistency_penalty` catches the domain mismatch perfectly, they might crack the Top 100 for a machine learning role.
2. **OOM on Scaling:** The engine currently loads the entire 116k `candidates.jsonl` into memory as a Pandas DataFrame for every request. While fine for a 5-minute hackathon challenge, it will OOM on a standard cloud VM under concurrent traffic.
3. **BM25 Tokenization Mismatch:** BM25 relies on exact term overlap. If the JD says "React.js" and the candidate says "ReactJS", the BM25 score drops to 0 for that term. Semantic search mitigates this, but BM25 is still brittle.
