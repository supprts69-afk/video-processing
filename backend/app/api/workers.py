# backend/app/api/workers.py
import secrets
import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
from app.database import get_db_connection

router = APIRouter(prefix="/api/v1/workers")

class RegisterRequest(BaseModel):
    name: str
    capabilities: dict = {}

class ClaimResponse(BaseModel):
    task_id: Optional[str]
    job_id: Optional[str]
    processing_params: Optional[dict]
    source_url: Optional[str]

@router.post("/register")
async def register_worker(req: RegisterRequest, db=Depends(get_db_connection)):
    """Colab থেকে নতুন Worker রেজিস্টার করা"""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    query = """
        INSERT INTO workers (name, capabilities, status, api_token_hash)
        VALUES (:name, :caps, 'idle', :hash)
        RETURNING id;
    """
    worker_id = await db.execute(query, {
        "name": req.name,
        "caps": json.dumps(req.capabilities),
        "hash": token_hash
    })
    return {"worker_id": str(worker_id), "token": raw_token}

async def update_worker_heartbeat(db, worker_id: str, status: str):
    await db.execute(
        "UPDATE workers SET last_heartbeat_at = now(), status = :status WHERE id = :id", 
        {"status": status, "id": worker_id}
    )

@router.post("/{worker_id}/heartbeat")
async def worker_heartbeat(worker_id: str, db=Depends(get_db_connection)):
    """Worker এর কানেকশন চেক করা"""
    await update_worker_heartbeat(db, worker_id, status="idle")
    return {"status": "ok"}

@router.post("/{worker_id}/claim", response_model=ClaimResponse)
async def claim_task(worker_id: str, db=Depends(get_db_connection)):
    """নতুন টাস্ক খোঁজা"""
    await update_worker_heartbeat(db, worker_id, status="busy")
    
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
    
    params = task["processing_params"]
    if isinstance(params, str):
        params = json.loads(params)

    return ClaimResponse(
        task_id=str(task["id"]),
        job_id=str(task["job_id"]),
        processing_params=params,
        source_url=job["source_url"]
    )
