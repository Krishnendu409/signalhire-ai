# Frontend Data Flow Audit

## 1. Current Frontend State Structure
- The `useWorkspaceStore` (`store/workspace.ts`) maintains an array of `Candidate` objects.
- A single `Candidate` type represents all UI rendering needs, merging identity, text narrative, technical evidence, and scores.
- State is managed via local React state hooks (`useState`) inside components for demo logic, rather than centralized in the store.

## 2. Current Backend Output Structure
- **Offline Output:** `candidate_embeddings.npy` (unusable directly by UI).
- **Online Output:** `submission.csv` containing: `candidate_id`, `rank`, `score`, and `reasoning`.
- **Database:** `candidates.jsonl` contains raw JSON objects representing the candidate's career history, skills, and profile.

## 3. Missing Mappings
- **Rank and Score:** Available in `submission.csv`, but missing for unranked candidates.
- **Evidence generation:** `reasoning` in `submission.csv` is a single paragraph. The UI expects structured evidence (`evidence.retrieval`, `evidence.ranking`, etc.). We will parse the `reasoning` string to populate structured arrays.
- **Identity mapping:** The UI needs names and titles, which exist in `candidates.jsonl`, but not in `submission.csv`. The repository layer must join these two sources.

## 4. Components Still Using Mock Data
- `store/workspace.ts` (`MOCK_CANDIDATES`)
- `app/page.tsx` (Hardcoded Landing Page copy)

## 5. Components Not Connected to State
- `page.tsx` (Completely detached from the real ranking engine)
- Workspace components rely on `selectedCandidate`, but the initialization of the list itself relies on hardcoded data, bypassing the backend.
