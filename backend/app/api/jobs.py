import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import get_db_connection

router = APIRouter(prefix="/api/v1/jobs")

class JobCreateRequest(BaseModel):
    source_url: str
    processing_profile: dict = {}

@router.post("")
async def create_job(req: JobCreateRequest, db=Depends(get_db_connection)):
    # নতুন জব তৈরি করা
    job_query = """
        INSERT INTO jobs (source_url, status, expected_task_count, completed_task_count)
        VALUES (:url, 'processing', 0, 0)
        RETURNING id;
    """
    job_id = await db.execute(job_query, {"url": req.source_url})
    
    # প্রথমে ভিডিওর দৈর্ঘ্য জানার জন্য একটি Probe টাস্ক তৈরি করা
    probe_params = json.dumps({"type": "probe"})
    task_query = """
        INSERT INTO tasks (job_id, status, processing_params)
        VALUES (:job_id, 'queued', :params)
    """
    await db.execute(task_query, {"job_id": job_id, "params": probe_params})
    
    return {"job_id": str(job_id), "message": "Probe task created successfully"}
