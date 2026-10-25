# backend/app/services/finalizer.py
import os
import subprocess
import requests
from app.api.cloudinary import upload_server_file

async def finalize_job(db, job_id: str):
    """Downloads segments, merges via FFmpeg concat protocol, and uploads to Cloudinary."""
    
    # 1. Lock the job to prevent duplicate finalization
    lock_query = """
        UPDATE jobs SET status = 'finalizing'
        WHERE id = :job_id AND status = 'processing'
          AND expected_task_count = completed_task_count
        RETURNING id;
    """
    job = await db.execute(lock_query, {"job_id": job_id})
    if not job:
        return # Job already finalizing or not ready
        
    # 2. Retrieve all segment URLs ordered by index
    tasks = await db.fetch_all(
        "SELECT task_index, output_url FROM tasks WHERE job_id = :job_id ORDER BY task_index ASC",
        {"job_id": job_id}
    )
    
    work_dir = f"/tmp/job_{job_id}"
    os.makedirs(work_dir, exist_ok=True)
    concat_file_path = os.path.join(work_dir, "concat.txt")
    
    try:
        # 3. Download segments and prepare concat text file
        with open(concat_file_path, "w") as f:
            for task in tasks:
                seg_path = os.path.join(work_dir, f"segment_{task['task_index']}.mp4")
                # Download file securely
                res = requests.get(task["output_url"], stream=True, timeout=30)
                with open(seg_path, "wb") as seg_file:
                    for chunk in res.iter_content(chunk_size=8192):
                        seg_file.write(chunk)
                f.write(f"file 'segment_{task['task_index']}.mp4'\n")

        # 4. Stream-copy concatenation
        final_output_path = os.path.join(work_dir, "final.mp4")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
            "-i", concat_file_path, "-c", "copy", final_output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Merge failed: {result.stderr}")

        # 5. Upload final asset & Mark Complete
        final_cloudinary_url = upload_server_file(final_output_path)
        await db.execute(
            "UPDATE jobs SET status = 'completed', final_video_url = :url WHERE id = :job_id",
            {"url": final_cloudinary_url, "job_id": job_id}
        )

    except Exception as e:
        await db.execute(
            "UPDATE jobs SET status = 'failed', error_message = :err WHERE id = :job_id",
            {"err": str(e), "job_id": job_id}
        )
    finally:
        # 6. Cleanup local temp files
        subprocess.run(["rm", "-rf", work_dir])
