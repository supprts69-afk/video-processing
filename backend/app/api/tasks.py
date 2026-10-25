# backend/app/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/v1/workers/tasks")

class ProgressReport(BaseModel):
    progress_percentage: float

@router.post("/{task_id}/progress")
async def report_progress(task_id: str, payload: ProgressReport, db=Depends(get_db_connection)):
    """Extends the lease duration for an active task."""
    new_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    query = """
        UPDATE tasks 
        SET lease_expires_at = :new_expiry, progress = :progress, updated_at = now()
        WHERE id = :task_id AND status = 'leased'
        RETURNING id;
    """
    result = await db.execute(query, {
        "task_id": task_id,
        "new_expiry": new_expiry,
        "progress": payload.progress_percentage
    })
    
    if not result:
        raise HTTPException(status_code=400, detail="Task lease expired or invalid state")
    return {"status": "lease_extended"}

async def recover_stale_tasks(db):
    """
    Background job: Sweeps the database for expired leases and returns 
    them to the queue if they haven't exceeded maximum attempts.
    """
    query = """
        UPDATE tasks 
        SET status = 'queued', worker_id = NULL
        WHERE status = 'leased' 
          AND lease_expires_at < now()
          AND attempt_count < max_attempts
        RETURNING id;
    """
    recovered = await db.fetch_all(query)
    
    # Mark tasks that exceeded retries as failed
    fail_query = """
        UPDATE tasks 
        SET status = 'failed', error_message = 'Max attempts exceeded'
        WHERE status = 'leased' 
          AND lease_expires_at < now()
          AND attempt_count >= max_attempts
        RETURNING job_id;
    """
    await db.execute(fail_query)
    
    return {"recovered": len(recovered)}
