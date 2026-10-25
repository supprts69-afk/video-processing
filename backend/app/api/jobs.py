# backend/app/api/jobs.py
import math
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_db_connection

router = APIRouter(prefix="/api/v1/jobs")

class ProcessingProfile(BaseModel):
    segment_duration: int = 30
    resolution: str = "1920x1080"
    codec: str = "libx264"
    preset: str = "fast"

class JobCreateRequest(BaseModel):
    source_url: str
    processing_profile: ProcessingProfile = ProcessingProfile()

@router.post("")
async def create_job(req: JobCreateRequest, db=Depends(get_db_connection)):
    """Creates a new video processing job and splits it into tasks."""
    # ডেমো পারপাসে ভিডিওর দৈর্ঘ্য ১২০ সেকেন্ড ধরা হয়েছে। 
    # প্রোডাকশনে FFprobe দিয়ে আসল URL-এর ডিউরেশন চেক করে নিতে হবে।
    duration_sec = 120.0 
    expected_tasks = math.ceil(duration_sec / req.processing_profile.segment_duration)
    
    # 1. Insert Job
    job_query = """
        INSERT INTO jobs (source_url, processing_profile, expected_task_count, status)
        VALUES (:source_url, :profile, :task_count, 'queued')
        RETURNING id;
    """
    job_id = await db.execute(job_query, {
        "source_url": req.source_url, 
        "profile": req.processing_profile.model_dump_json(), 
        "task_count": expected_tasks
    })
    
    # 2. Generate and Insert Tasks
    tasks_to_insert = []
    for i in range(expected_tasks):
        start_time = i * req.processing_profile.segment_duration
        duration = min(req.processing_profile.segment_duration, duration_sec - start_time)
        
        processing_params = {
            "start": start_time,
            "duration": duration,
            "resolution": req.processing_profile.resolution,
            "codec": req.processing_profile.codec
        }
        
        tasks_to_insert.append({
            "job_id": job_id,
            "task_index": i,
            "params": processing_params  # Dictionary হিসেবে পাস করা হলো
        })
    
    task_query = """
        INSERT INTO tasks (job_id, task_index, processing_params, status)
        VALUES (:job_id, :task_index, :params, 'queued');
    """
    # JSON সিরিয়ালাইজেশনের জন্য pydantic বা json ব্যবহার করা ডাটাবেস ড্রাইভারের উপর নির্ভর করে
    # asyncpg jsonb ফিল্ডে ডিকশনারি সাপোর্ট করে
    import json
    for t in tasks_to_insert:
        t["params"] = json.dumps(t["params"])

    await db.execute_many(task_query, tasks_to_insert)
    
    return {"job_id": str(job_id), "tasks_created": expected_tasks}

@router.get("/{job_id}")
async def get_job(job_id: str, db=Depends(get_db_connection)):
    """Fetches job details."""
    query = "SELECT * FROM jobs WHERE id = :job_id"
    job = await db.fetch_one(query, {"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return dict(job)
