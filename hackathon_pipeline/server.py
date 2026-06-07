import asyncio
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from engine import RankingEngine

app = FastAPI(title="SignalHire Ranking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory investigation storage
investigation_store: Dict[str, Dict[str, Any]] = {}

# Lazy-loaded engine
engine = None

def get_engine():
    global engine
    if engine is None:
        engine = RankingEngine()
    return engine

class JDRequest(BaseModel):
    raw_text: str

def parse_jd_text(raw_text: str) -> dict:
    import re
    eng = get_engine()
    raw_lower = raw_text.lower()
    
    family = "Unknown"
    for fam, terms in eng.config['role_families'].items():
        if any(t.lower() in raw_lower for t in terms):
            family = fam
            break
            
    if family == "Unknown":
        family = "Search Engineer"
        
    title_terms = eng.config['role_families'].get(family, [])
    req_skills = eng.config['skill_families'].get(family, [])
    
    custom_skills = []
    match = re.search(r'skills:\s*(.*)', raw_text, re.IGNORECASE)
    if match:
        custom_skills = [s.strip().lower() for s in match.group(1).split(',')]
        
    keywords = list(set(req_skills + custom_skills))
    
    return {
        "family": family,
        "keywords": keywords,
        "title_terms": title_terms,
        "req_skills": req_skills
    }

def run_investigation(investigation_id: str, jd_data: dict):
    try:
        investigation_store[investigation_id]["status"] = "RUNNING"
        eng = get_engine()
        results = eng.run_pipeline(jd_data)
        
        investigation_store[investigation_id]["status"] = "COMPLETED"
        investigation_store[investigation_id]["results"] = results
    except Exception as e:
        investigation_store[investigation_id]["status"] = "FAILED"
        investigation_store[investigation_id]["error"] = str(e)
        print(f"Investigation {investigation_id} failed: {e}")

@app.post("/api/investigations")
async def start_investigation(jd_req: JDRequest, background_tasks: BackgroundTasks):
    investigation_id = str(uuid.uuid4())
    investigation_store[investigation_id] = {
        "status": "PENDING",
        "results": None,
        "error": None
    }
    
    parsed_data = parse_jd_text(jd_req.raw_text)
    
    # Send to background task
    background_tasks.add_task(run_investigation, investigation_id, parsed_data)
    
    return {"investigation_id": investigation_id, "status": "PENDING"}

@app.get("/api/investigations/{investigation_id}/status")
async def get_status(investigation_id: str):
    if investigation_id not in investigation_store:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    inv = investigation_store[investigation_id]
    return {"investigation_id": investigation_id, "status": inv["status"]}

@app.get("/api/investigations/{investigation_id}/results")
async def get_results(investigation_id: str):
    if investigation_id not in investigation_store:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    inv = investigation_store[investigation_id]
    
    if inv["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"Investigation is {inv['status']}, not COMPLETED")
        
    return {"investigation_id": investigation_id, "results": inv["results"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
