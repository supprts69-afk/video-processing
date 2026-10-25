import json
from fastapi import APIRouter, Depends, Response, HTTPException
from pydantic import BaseModel
from app.database import get_db_connection

router = APIRouter(prefix="/api/v1/jobs")

class JobCreateRequest(BaseModel):
    source_url: str
    processing_profile: dict = {}

@router.post("")
async def create_job(req: JobCreateRequest, db=Depends(get_db_connection)):
    try:
        # প্যারামিটার দিয়ে status পাস করা হলো যাতে ENUM টাইপ এরর না হয়
        job_query = """
            INSERT INTO jobs (source_url, status, expected_task_count, completed_task_count)
            VALUES (:url, :status, 0, 0)
            RETURNING id;
        """
        job_id = await db.execute(job_query, {"url": req.source_url, "status": "processing"})
        
        if not job_id:
            raise Exception("Failed to generate job_id from database")
            
        probe_params = json.dumps({"type": "probe"})
        task_query = """
            INSERT INTO tasks (job_id, status, processing_params)
            VALUES (:job_id, :task_status, CAST(:params AS JSON))
        """
        await db.execute(task_query, {
            "job_id": job_id, 
            "task_status": "queued",
            "params": probe_params
        })
        
        return {"job_id": str(job_id), "message": "Probe task created successfully"}
        
    except Exception as e:
        error_msg = str(e)
        print(f">>> EXACT DB ERROR: {error_msg} <<<")
        raise HTTPException(status_code=500, detail=f"Database Error: {error_msg}")

@router.get("/{job_id}/playlist.m3u8")
async def get_hls_playlist(job_id: str, db=Depends(get_db_connection)):
    """Completed খণ্ডগুলো দিয়ে ডায়নামিক HLS Playlist তৈরি করা"""
    query = """
        SELECT processing_params, output_url 
        FROM tasks 
        WHERE job_id = :job_id AND status = 'completed' AND output_url IS NOT NULL
    """
    tasks = await db.fetch_all(query, {"job_id": job_id})
    
    segments = []
    for t in tasks:
        params = json.loads(t["processing_params"])
        if params.get("type") == "process":
            segments.append({
                "index": params.get("segment_index", 0),
                "duration": params.get("duration", 15.0),
                "url": t["output_url"]
            })
            
    # পার্ট অনুযায়ী সাজানো
    segments.sort(key=lambda x: x["index"])
    
    if not segments:
        return Response(content="", status_code=404)
        
    target_duration = int(max([s["duration"] for s in segments]) + 1)
    
    # m3u8 ফাইল জেনারেট করা
    m3u8 = "#EXTM3U\n"
    m3u8 += "#EXT-X-VERSION:3\n"
    m3u8 += f"#EXT-X-TARGETDURATION:{target_duration}\n"
    m3u8 += "#EXT-X-MEDIA-SEQUENCE:0\n"
    
    for s in segments:
        m3u8 += f"#EXTINF:{s['duration']:.6f},\n"
        m3u8 += f"{s['url']}\n"
        
    m3u8 += "#EXT-X-ENDLIST\n"
    
    return Response(content=m3u8, media_type="application/vnd.apple.mpegurl")
