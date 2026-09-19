import asyncio
import uuid
from typing import Any, Callable, Coroutine
from backend.app import db

def create_job(kind: str) -> str:
    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "kind": kind,
        "status": "queued",
        "stage": "started",
        "progress": 0.0,
        "result": None,
        "error": None
    }
    db.save_doc(job_id, "job", job_data)
    return job_id

def update_job(job_id: str, **kwargs):
    job = db.get_doc(job_id)
    if job:
        job.update(kwargs)
        db.save_doc(job_id, "job", job)

def get_progress_callback(job_id: str) -> Callable[[str, float], None]:
    def cb(stage: str, progress: float):
        update_job(job_id, stage=stage, progress=progress)
    return cb

async def run_background_task(job_id: str, coro: Coroutine[Any, Any, Any]):
    try:
        update_job(job_id, status="running")
        result = await coro
        # Extract model_dump if it's a pydantic model
        if hasattr(result, "model_dump"):
            result = result.model_dump(mode="json")
        update_job(job_id, status="done", progress=1.0, stage="done", result=result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        update_job(job_id, status="error", error=str(e))

def dispatch_job(job_id: str, coro: Coroutine[Any, Any, Any]):
    asyncio.create_task(run_background_task(job_id, coro))
