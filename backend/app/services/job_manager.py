# backend/app/services/job_manager.py
import math
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List

class ProcessingProfile(BaseModel):
    segment_duration: int = 30
    resolution: str = "1920x1080"
    codec: str = "libx264"
    preset: str = "fast"

async def create_job_and_tasks(db, source_url: str, duration_sec: float, profile: ProcessingProfile):
    """Creates a job and splits the video into distributed tasks."""
    
    # Calculate the number of segments required
    expected_tasks = math.ceil(duration_sec / profile.segment_duration)
    
    # 1. Insert Job
    job_query = """
        INSERT INTO jobs (source_url, processing_profile, expected_task_count, status)
        VALUES (:source_url, :profile, :task_count, 'queued')
        RETURNING id;
    """
    job_id = await db.execute(job_query, {
        "source_url": source_url, 
        "profile": profile.model_dump_json(), 
        "task_count": expected_tasks
    })
    
    # 2. Generate and Insert Tasks
    tasks_to_insert = []
    for i in range(expected_tasks):
        start_time = i * profile.segment_duration
        duration = min(profile.segment_duration, duration_sec - start_time)
        
        processing_params = {
            "start": start_time,
            "duration": duration,
            "resolution": profile.resolution,
            "codec": profile.codec
        }
        
        tasks_to_insert.append({
            "job_id": job_id,
            "task_index": i,
            "processing_params": processing_params
        })
    
    # Bulk insert tasks
    task_query = """
        INSERT INTO tasks (job_id, task_index, processing_params, status)
        VALUES (:job_id, :task_index, :params, 'queued');
    """
    await db.execute_many(task_query, tasks_to_insert)
    
    return {"job_id": job_id, "tasks_created": expected_tasks}
