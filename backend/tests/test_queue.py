# backend/tests/test_queue.py
import asyncio
import pytest
from app.api.workers import claim_task
from app.database import get_db_connection

@pytest.mark.asyncio
async def test_concurrent_task_claiming():
    """
    Ensures that if multiple workers request a task at the exact same millisecond,
    PostgreSQL FOR UPDATE SKIP LOCKED prevents double-assignment.
    """
    db = await get_db_connection()
    
    # Assume job and 1 queued task exist in the test DB
    worker_id_1 = "worker_alpha"
    worker_id_2 = "worker_beta"
    
    # Simulate simultaneous HTTP requests hitting the DB
    results = await asyncio.gather(
        claim_task(worker_id_1, db),
        claim_task(worker_id_2, db)
    )
    
    claimed_tasks = [res.task_id for res in results if res.task_id is not None]
    
    # Only one worker should successfully claim the task
    assert len(claimed_tasks) == 1, "Concurrency failure: Task was claimed by multiple workers"
    
    # Verify the database state reflects the lease
    task_record = await db.fetch_one("SELECT status, worker_id FROM tasks WHERE id = :id", {"id": claimed_tasks[0]})
    assert task_record["status"] == "leased"
    assert task_record["worker_id"] in [worker_id_1, worker_id_2]
