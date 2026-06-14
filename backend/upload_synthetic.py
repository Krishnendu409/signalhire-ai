import asyncio
import json
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text
from app.core.config import settings
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
import uuid

# Re-use backend engine configuration
engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

API_BASE = "http://localhost:8000/api"

synthetic_candidates = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "parsed_data": {
            "full_name": "Alice Synthetic",
            "current_title": "Search Engineer",
            "experiences": [
                {
                    "title": "Search Engineer",
                    "company": "FakeCorp",
                    "bullets": ["Built a massive RAG pipeline", "Scaled vector search using FAISS"]
                }
            ],
            "skills": [
                {"name": "FAISS"},
                {"name": "Python"},
                {"name": "Machine Learning"}
            ]
        }
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "parsed_data": {
            "full_name": "Bob Synthetic",
            "current_title": "HR Manager",
            "experiences": [
                {
                    "title": "HR Manager",
                    "company": "RecruitingCo",
                    "bullets": ["Managed 50 employees", "Organized team building events"]
                }
            ],
            "skills": [
                {"name": "Management"},
                {"name": "HR"}
            ]
        }
    }
]

async def main():
    async with async_session() as db:
        # Get system user
        res = await db.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        if not user:
            print("No user found in DB. Creating system user...")
            user = User(id=uuid.uuid4(), email="admin@synthetic.local", hashed_password="pwd")
            db.add(user)
            await db.commit()
            
        print(f"Using Recruiter ID: {user.id}")

        # Delete old synthetic candidates to ensure clean state
        await db.execute(text("DELETE FROM candidates WHERE id = '00000000-0000-0000-0000-000000000001' OR id = '00000000-0000-0000-0000-000000000002'"))
        await db.commit()
        
        # Disable all other candidates for this recruiter to strictly test upload bypass
        await db.execute(text("UPDATE candidates SET parsed_data = NULL WHERE recruiter_id = :uid"), {"uid": str(user.id)})
        await db.commit()

        # Insert Synthetic Candidates
        for c_data in synthetic_candidates:
            cand = Candidate(
                id=uuid.UUID(c_data["id"]),
                recruiter_id=user.id,
                resume_file_key="fake-key",
                parsed_data=c_data["parsed_data"]
            )
            db.add(cand)
            print(f"Inserted synthetic candidate: {c_data['id']}")
            
        await db.commit()
        
        # Ensure a job exists
        res = await db.execute(select(Job).where(Job.recruiter_id == user.id).limit(1))
        job = res.scalar_one_or_none()
        if not job:
            job = Job(
                id=uuid.uuid4(),
                recruiter_id=user.id,
                title="Search Engineer",
                parsed_requirements={"title": "Search Engineer", "required_hard_skills": ["FAISS", "Python"]}
            )
            db.add(job)
            await db.commit()
            
        print(f"Using Job ID: {job.id}")
        
    print("\n--- Triggering Ranking via API ---")
    headers = {"Authorization": "Bearer demo-token-placeholder"}
    async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
        res = await client.post(f"{API_BASE}/rankings/{job.id}")
        print("POST response:", res.json())
        
        status = "pending"
        latest_data = None
        while status in ["pending", "processing"]:
            await asyncio.sleep(2)
            res = await client.get(f"{API_BASE}/rankings/{job.id}/latest")
            latest_data = res.json()
            status = latest_data.get("status")
            print("Polled Status:", status)
            
        print("\n--- Final Ranking Response ---")
        results = latest_data.get("results", [])
        print(f"Returned {len(results)} candidates.")
        
        with open("SYNTHETIC_DATASET_RESULTS.json", "w") as f:
            json.dump(latest_data, f, indent=2)
            
        print("Saved to SYNTHETIC_DATASET_RESULTS.json")
            
if __name__ == "__main__":
    asyncio.run(main())
