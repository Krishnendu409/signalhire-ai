# Mock Data Audit

## Current Instances of Mock Data

### 1. `store/workspace.ts`
- Line 74: `const MOCK_CANDIDATES: Candidate[] = [...]`
- The entire array is hardcoded with pseudo-profiles like "Sarah Chen" and "Kevin Park".
- Hardcoded decision paths, evidence, and narratives.

### 2. `app/page.tsx`
- Hardcoded string: `"Marketing Manager"`
- Hardcoded string: `"ATS SCORE: 78%"`
- Hardcoded string: `"Search Engineer"`
- Hardcoded string: `"MATCH SCORE: 96%"`
- Hardcoded feature tags: `FAISS`, `Qdrant`, `Learning-to-Rank`

### Elimination Strategy
All hardcoded candidates in `store/workspace.ts` will be deleted.
All hardcoded narrative points in `page.tsx` will be wired to read directly from `demo_cases.json` via the `useWorkspaceStore`.
