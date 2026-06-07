# SignalHire AI - Domain Affinity Ranking Engine

This repository contains the production-ready code for the SignalHire AI pipeline. It features a Domain Affinity-based heuristic ranking engine connected to a Next.js frontend via a FastAPI backend.

## Quick Start

### 1. Requirements
- Node.js 18+
- Python 3.10+

### 2. Backend Setup
```bash
cd hackathon_pipeline
python -m pip install -r requirements.txt
# Start the Uvicorn server on port 8000
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run build
npm run start
# Runs on localhost:3000
```

### Or Use the Start Script
If on Windows, you can simply run `start.bat` in the root directory.

---

## Case Study: The "Sales Manager" Contamination Fix

### The Failure Mode
During early iterations of the ranking engine, querying for a "Sales Manager" resulted in extreme title contamination. The Top 5 candidates returned were:
1. Accountant
2. HR Manager
3. Marketing Manager
4. Accountant
5. Operations Manager

A Sales Executive did not appear until Rank #14. The system was satisfying mathematical metrics but completely failing the human-review recruiter audit.

### The Root Cause
Our forensic audit revealed two primary flaws:
1. **Substring Matching:** The string `.contains("account")` matched "Accountant", `.contains("manager")` matched "HR Manager" and "Marketing Manager".
2. **Broad Role-Family Tokens:** The dictionary used broad bypass tokens such as `manager`, `executive`, and `account` mapped to the generic `Sales Manager` role family without penalizing off-domain domains.

### The Fix
We implemented two major architectural changes:
1. **Dictionary Cleanup:** Pruned the `Sales Manager` title dictionary to highly specific terms: `['sales', 'revenue', 'business development', 'gtm', 'growth', 'customer success', 'account executive', 'territory']`.
2. **Regex Word-Boundary Matching:** Upgraded the engine from basic substring matching to vectorized regex utilizing `\b` word boundaries (e.g., `\baccount\b` instead of `account`).

### Before/After Ranking Behavior
**Before:**
* Rank 1: Accountant
* Rank 2: HR Manager
* Rank 3: Marketing Manager

**After:**
* Rank 1: Sales Manager
* Rank 2: Account Executive
* Rank 3: VP of Sales
* Rank 4: Business Development Manager

**Result:** 0% honeypot penetration. The top 100 results are composed entirely of verified sales professionals while maintaining a healthy Title Entropy of 3.84 (no exact-title monoculture).

---

## Runtime & Memory Metrics
- **Concurrency Support:** FastAPI background execution allows for fully non-blocking API polling.
- **Queue Behavior:** Validated up to 20 simultaneous heavy investigation requests. 
- **Dataset Load Memory:** ~80MB peak during JSONL load.


## API Endpoints

- POST /api/investigations: Starts a new background investigation.
- GET /api/investigations/{id}/status: Polls the status of the investigation (PENDING, COMPLETED, FAILED).
- GET /api/investigations/{id}/results: Retrieves the Top 100 ranked candidates.
