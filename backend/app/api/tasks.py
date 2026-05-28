from fastapi import APIRouter, HTTPException
from app.tasks.manager import task_queue

router = APIRouter()

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Poll for the status of a background task."""
    status = task_queue.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status
