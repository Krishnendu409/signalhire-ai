import asyncio
import uuid
from typing import Any, Dict, Callable

class SimpleQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.tasks: Dict[str, Dict[str, Any]] = {}

    async def add_task(self, name: str, func: Callable, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "id": task_id,
            "name": name,
            "status": "pending",
            "progress": 0,
            "result": None,
            "error": None
        }
        await self.queue.put((task_id, func, args, kwargs))
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any] | None:
        return self.tasks.get(task_id)

    async def update_task(self, task_id: str, **kwargs):
        if task_id in self.tasks:
            self.tasks[task_id].update(kwargs)

# Global queue instance
task_queue = SimpleQueue()
