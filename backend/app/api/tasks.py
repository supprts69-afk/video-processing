import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import get_db_connection

router = APIRouter(prefix="/api/v1/workers/tasks")

class TaskCompleteRequest(BaseModel):
    output_url: Optional[str] = None
    duration: Optional[float] = None

@router.post("/{task_id}/complete")
async def complete_task(task_id: str, req: TaskCompleteRequest, db=Depends(get_db_connection)):
    task_query = """
        UPDATE tasks SET status = 'completed', output_url = :url, updated_at = now() 
        WHERE id = :task_id AND status = 'leased' 
        RETURNING job_id, processing_params;
    """
    task_record = await db.fetch_one(task_query, {"task_id": task_id, "url": req.output_url or ""})
    if not task_record:
        raise HTTPException(status_code=400, detail="Invalid task state")
        
    job_id = task_record["job_id"]
    params = task_record["processing_params"]
    if isinstance(params, str):
        params = json.loads(params)

    if params.get("type") == "probe":
        total_duration = req.duration or 0.0
        
        workers_query = "SELECT count(*) FROM workers WHERE last_heartbeat_at > now() - interval '2 minutes'"
        active_workers = await db.fetch_val(workers_query)
        if active_workers == 0:
            active_workers = 1 
            
        segment_duration = total_duration / active_workers
        
        # task_index যুক্ত করা হলো
        task_insert_query = """
            INSERT INTO tasks (job_id, task_index, status, processing_params)
            VALUES (:job_id, :t_index, 'queued', CAST(:params AS JSON))
        """
        for i in range(active_workers):
            start_time = i * segment_duration
            proc_params = json.dumps({
                "type": "process",
                "start": start_time,
                "duration": segment_duration,
                "segment_index": i + 1
            })
            await db.execute(task_insert_query, {
                "job_id": job_id, 
                "t_index": i + 1,
                "params": proc_params
            })
            
        await db.execute(
            "UPDATE jobs SET expected_task_count = :count WHERE id = :job_id",
            {"count": active_workers, "job_id": job_id}
        )
        return {"status": "success", "message": f"Video divided into {active_workers} parts"}

    else:
        job_query = """
            UPDATE jobs SET completed_task_count = completed_task_count + 1 
            WHERE id = :job_id 
            RETURNING expected_task_count, completed_task_count;
        """
        job = await db.fetch_one(job_query, {"job_id": job_id})
        
        if job["completed_task_count"] >= job["expected_task_count"]:
            await db.execute("UPDATE jobs SET status = 'completed' WHERE id = :job_id", {"job_id": job_id})
            
        return {"status": "success"}

class TaskFailRequest(BaseModel):
    error: str

@router.post("/{task_id}/fail")
async def fail_task(task_id: str, req: TaskFailRequest, db=Depends(get_db_connection)):
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
