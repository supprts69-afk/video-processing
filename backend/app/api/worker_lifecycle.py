# backend/app/api/worker_lifecycle.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import secrets
import hashlib

router = APIRouter(prefix="/api/v1/workers")

class RegisterRequest(BaseModel):
    name: str
    capabilities: dict = {}

@router.post("/register")
async def register_worker(req: RegisterRequest, db=Depends(get_db_connection)):
    """Registers a new worker and returns a single-use connection token."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    query = """
        INSERT INTO workers (name, capabilities, status, api_token_hash)
        VALUES (:name, :caps, 'idle', :hash)
        RETURNING id;
    """
    worker_id = await db.execute(query, {
        "name": req.name,
        "caps": req.capabilities,
        "hash": token_hash
    })
    
    # The raw token is returned EXACTLY once. It is never stored in plaintext.
    return {"worker_id": str(worker_id), "token": raw_token}

class TaskCompleteRequest(BaseModel):
    output_url: str

@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, req: TaskCompleteRequest, db=Depends(get_db_connection)):
    """Marks a task as complete and increments the job progress atomically."""
    # 1. Mark task complete
    task_query = """
        UPDATE tasks SET status = 'completed', output_url = :url, updated_at = now()
        WHERE id = :task_id AND status = 'leased'
        RETURNING job_id;
    """
    job_id = await db.execute(task_query, {"task_id": task_id, "url": req.output_url})
    if not job_id:
        raise HTTPException(status_code=400, detail="Invalid task state or expired lease")

    # 2. Increment job completion count
    job_query = """
        UPDATE jobs SET completed_task_count = completed_task_count + 1
        WHERE id = :job_id
        RETURNING id, expected_task_count, completed_task_count;
    """
    job_state = await db.fetch_one(job_query, {"job_id": job_id})
    
    # Trigger finalization if all tasks are complete
    if job_state["completed_task_count"] == job_state["expected_task_count"]:
        # Trigger async finalization queue/worker here
        pass

    return {"status": "success"}

class TaskFailRequest(BaseModel):
    error: str

@router.post("/tasks/{task_id}/fail")
async def fail_task(task_id: str, req: TaskFailRequest, db=Depends(get_db_connection)):
    """Fails a task, returning it to the queue if attempts remain."""
    query = """
        UPDATE tasks 
        SET status = CASE WHEN attempt_count < max_attempts THEN 'queued'::task_status ELSE 'failed'::task_status END,
            worker_id = NULL,
            error_message = :err,
            updated_at = now()
        WHERE id = :task_id AND status = 'leased'
        RETURNING status;
    """
    new_status = await db.execute(query, {"task_id": task_id, "err": req.error})
    return {"new_status": new_status}
