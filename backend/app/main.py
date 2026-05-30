import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import jobs, candidates, rankings, tasks, feedback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("signalhire")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SignalHire AI backend...")
    from app.services.vector_store import init_qdrant
    from app.services.reranker import warmup_reranker
    await init_qdrant()
    await asyncio.to_thread(warmup_reranker)
    yield
    logger.info("Shutting down SignalHire AI backend...")

app = FastAPI(title="SignalHire AI", version="1.0.0", lifespan=lifespan)

# Explicit CORS origins – this fixes the "Failed to fetch" error
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(rankings.router, prefix="/api/rankings", tags=["rankings"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}