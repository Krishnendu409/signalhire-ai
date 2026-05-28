import asyncio
import logging
from app.tasks.manager import task_queue

logger = logging.getLogger("signalhire.worker")

async def worker_loop():
    """Continuously pulls tasks from the queue and executes them."""
    logger.info("Background worker starting...")
    while True:
        try:
            task_id, func, args, kwargs = await task_queue.queue.get()
            
            await task_queue.update_task(task_id, status="processing")
            logger.info(f"Processing task {task_id}")
            
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                await task_queue.update_task(task_id, status="completed", progress=100, result=result)
                logger.info(f"Task {task_id} completed")
            except Exception as e:
                logger.error(f"Task {task_id} failed: {str(e)}")
                await task_queue.update_task(task_id, status="failed", error=str(e))
            finally:
                task_queue.queue.task_done()
        except Exception as e:
            logger.error(f"Worker loop error: {str(e)}")
            await asyncio.sleep(1)

def start_worker():
    """Utility to start the worker in the background."""
    asyncio.create_task(worker_loop())
