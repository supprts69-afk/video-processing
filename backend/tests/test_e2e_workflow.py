# backend/tests/test_e2e_workflow.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_full_video_processing_lifecycle():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Register Worker
        reg_res = await client.post("/api/v1/workers/register", json={"name": "test_worker"})
        assert reg_res.status_code == 200
        worker_data = reg_res.json()
        headers = {"Authorization": f"Bearer {worker_data['token']}"}
        
        # 2. Create Job
        job_res = await client.post(
            "/api/v1/jobs", 
            json={"source_url": "http://example.com/vid.mp4", "processing_profile": {"segment_duration": 10}},
            headers={"X-Admin-Secret": "mock_secret"}
        )
        job_id = job_res.json()["job_id"]
        
        # 3. Worker Claims Task
        claim_res = await client.post(f"/api/v1/workers/{worker_data['worker_id']}/claim", headers=headers)
        task_id = claim_res.json()["task_id"]
        assert task_id is not None
        
        # 4. Worker Completes Task
        comp_res = await client.post(
            f"/api/v1/workers/tasks/{task_id}/complete", 
            json={"output_url": "mock_cloudinary_url"},
            headers=headers
        )
        assert comp_res.status_code == 200
        
        # 5. Verify Job Progress
        status_res = await client.get(f"/api/v1/jobs/{job_id}")
        assert status_res.json()["completed_task_count"] == 1
