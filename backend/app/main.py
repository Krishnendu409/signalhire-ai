from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import jobs, candidates, rankings, tasks, feedback

app = FastAPI(title="SignalHire AI", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    from app.tasks.worker import start_worker
    from app.services.vector_store import init_qdrant
    await init_qdrant()
    start_worker()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(rankings.router, prefix="/api/rankings", tags=["rankings"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}