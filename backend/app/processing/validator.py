# backend/app/processing/validator.py
import subprocess
import json

def validate_video_file(file_path: str, expected_codec: str = "h264") -> bool:
    """Uses FFprobe to verify file integrity and stream properties."""
    cmd = [
        "ffprobe", 
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height",
        "-of", "json",
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False
            
        metadata = json.loads(result.stdout)
        streams = metadata.get("streams", [])
        
        if not streams:
            return False
            
        video_stream = streams[0]
        if video_stream.get("codec_name") != expected_codec:
            return False
            
        return True
    except Exception:
        return False
