import uuid
import traceback
import asyncio
from app.tasks.functions import process_resume, process_ranking


class TaskManager:
    """In-memory task queue that matches the SAQ interface."""
    
    def __init__(self):
        self._tasks = {}
        self._functions = {
            "process_resume": process_resume,
            "process_ranking": process_ranking,
        }

    async def add_task(self, name: str, *args, **kwargs) -> str:
        """Enqueue a task and return its ID."""
        task_id = str(uuid.uuid4())
        func = self._functions.get(name)
        
        if not func:
            raise ValueError(f"Unknown task: {name}")
        
        # Store task state
        self._tasks[task_id] = {
            "id": task_id,
            "status": "pending",
            "result": None,
            "error": None,
        }
        
        # Run in background
        asyncio.create_task(self._run_task(task_id, func, *args, **kwargs))
        
        return task_id

    async def _run_task(self, task_id: str, func, *args, **kwargs):
        """Execute a task and update its status."""
        self._tasks[task_id]["status"] = "processing"
        try:
            result = await func(*args, **kwargs)
            self._tasks[task_id]["status"] = "completed"
            self._tasks[task_id]["result"] = result
        except Exception as e:
            traceback.print_exc()
            self._tasks[task_id]["status"] = "failed"
            self._tasks[task_id]["error"] = str(e)

    async def get_task_status(self, task_id: str) -> dict | None:
        """Get the current status of a task."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        return {
            "id": task["id"],
            "status": task["status"],
            "progress": 100 if task["status"] == "completed" else 0,
            "result": task["result"],
            "error": task["error"],
        }


# Global instance
task_queue = TaskManager()