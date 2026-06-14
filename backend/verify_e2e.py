import asyncio
import httpx
import json
import time

API_BASE = "http://localhost:8000/api"

async def run_verification():
    headers = {"Authorization": "Bearer demo-token-placeholder"}
    async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
        print("=== 1. Fetching Existing Job ===")
        res = await client.get(f"{API_BASE}/jobs/")
        jobs = res.json()
        print("GET /jobs Response:", json.dumps(jobs))
        if not jobs:
            print("No jobs found to test with.")
            return
            
        job_id = jobs[0].get("id")

        print(f"\n=== 2. Triggering Ranking for Job {job_id} ===")
        res = await client.post(f"{API_BASE}/rankings/{job_id}")
        rank_data = res.json()
        print("POST /rankings/{job_id} Response:", json.dumps(rank_data))

        print("\n=== 3. Polling Ranking Status ===")
        status = "pending"
        latest_data = None
        while status in ["pending", "processing"]:
            await asyncio.sleep(2)
            res = await client.get(f"{API_BASE}/rankings/{job_id}/latest")
            latest_data = res.json()
            status = latest_data.get("status")
            print("Polled Status:", status)
        
        print("\n=== 4. Final Ranking Response (Truncated) ===")
        print("Total candidates processed:", latest_data.get("total_candidates"))
        results = latest_data.get("results", [])
        print("Number of results returned:", len(results))
        if results:
            print("Top 1 Result JSON:", json.dumps(results[0], indent=2))
        
        # Save to file for further inspection
        with open("e2e_verification_output.json", "w") as f:
            json.dump(latest_data, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_verification())
