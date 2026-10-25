# backend/app/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

# ডাটাবেস কানেকশন ইমপোর্ট করা হলো
from app.database import get_db_connection

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
