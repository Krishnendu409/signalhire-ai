"""
100k Pipeline API Routes
=========================
POST /api/pipeline/run-100k  — triggers the pipeline in background
GET  /api/pipeline/100k-status — polls progress & results
GET  /api/pipeline/100k-results — returns full structured results for analytics/reports
"""

from fastapi import APIRouter, BackgroundTasks
from app.services.pipeline_100k import get_pipeline_state, run_100k_pipeline

router = APIRouter()


@router.post("/run-100k")
async def trigger_100k_pipeline(background_tasks: BackgroundTasks):
    """
    Trigger the 100k candidate ranking pipeline in the background.
    Returns immediately — poll /api/pipeline/100k-status for progress.
    """
    state = get_pipeline_state()
    if state["status"] == "running":
        return {
            "message": "Pipeline is already running.",
            "status": "running",
            "progress": state["progress"],
            "stage": state["stage"],
        }

    # Fire-and-forget via FastAPI BackgroundTasks
    background_tasks.add_task(run_100k_pipeline)

    return {
        "message": "100k pipeline started in background.",
        "status": "running",
    }


@router.get("/100k-status")
async def get_100k_status():
    """Poll the current state of the 100k pipeline."""
    state = get_pipeline_state()

    # Don't send full results in the status poll (can be large)
    return {
        "status": state["status"],
        "progress": state["progress"],
        "stage": state["stage"],
        "error": state["error"],
        "has_results": state["results"] is not None,
        "elapsed_seconds": (
            round(state["results"]["elapsed_seconds"], 1)
            if state.get("results") and state["results"].get("elapsed_seconds")
            else None
        ),
    }


@router.get("/100k-results")
async def get_100k_results():
    """
    Return the full structured results once the pipeline has completed.
    Used by Analytics and Reports pages.
    """
    state = get_pipeline_state()
    if state["status"] != "completed" or state["results"] is None:
        return {
            "status": state["status"],
            "progress": state["progress"],
            "stage": state["stage"],
            "error": state["error"],
        }

    results = state["results"]
    return {
        "status": "completed",
        "analytics": results.get("analytics", {}),
        "results": results.get("results", []),
        "total_evaluated": results.get("total_evaluated", 0),
        "retrieved": results.get("retrieved", 0),
        "ranked": results.get("ranked", 0),
        "shortlisted": results.get("shortlisted", 0),
        "elapsed_seconds": results.get("elapsed_seconds", 0),
        "model": results.get("model", ""),
        "scoring_method": results.get("scoring_method", ""),
        "used_lgbm": results.get("used_lgbm", False),
    }

