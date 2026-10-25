# backend/app/api/workers.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone

# ডাটাবেস কানেকশন ইমপোর্ট করা হলো
from app.database import get_db_connection

router = APIRouter(prefix="/api/v1/workers")

class ClaimResponse(BaseModel):
    task_id: Optional[str]
    job_id: Optional[str]
    processing_params: Optional[dict]
    source_url: Optional[str]

async def update_worker_heartbeat(db, worker_id: str, status: str):
    await db.execute("UPDATE workers SET last_heartbeat_at = now(), status = :status WHERE id = :id", {"status": status, "id": worker_id})

@router.post("/{worker_id}/claim", response_model=ClaimResponse)
async def claim_task(worker_id: str, db=Depends(get_db_connection)):
    # 1. Verify worker identity and update heartbeat
    await update_worker_heartbeat(db, worker_id, status="busy")
    
    # 2. Atomic claim using SKIP LOCKED
    query = """
        UPDATE tasks 
        SET 
            status = 'leased', 
            worker_id = :worker_id, 
            lease_expires_at = :lease_expiry,
            attempt_count = attempt_count + 1
        WHERE id = (
            SELECT id FROM tasks 
            WHERE status = 'queued' 
               OR (status = 'leased' AND lease_expires_at < :now)
            ORDER BY created_at ASC 
            FOR UPDATE SKIP LOCKED 
            LIMIT 1
        )
        RETURNING id, job_id, processing_params;
    """
    
    now = datetime.now(timezone.utc)
    lease_expiry = now + timedelta(minutes=10)
    
    task = await db.fetch_one(query, {"worker_id": worker_id, "now": now, "lease_expiry": lease_expiry})
    
    if not task:
        await update_worker_heartbeat(db, worker_id, status="idle")
        return ClaimResponse(task_id=None, job_id=None, processing_params=None, source_url=None)
        
    job = await db.fetch_one("SELECT source_url FROM jobs WHERE id = :job_id", {"job_id": task["job_id"]})
    
    return ClaimResponse(
        task_id=str(task["id"]),
        job_id=str(task["job_id"]),
        processing_params=task["processing_params"],
        source_url=job["source_url"]
    )
