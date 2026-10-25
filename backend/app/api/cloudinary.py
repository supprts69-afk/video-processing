# backend/app/api/cloudinary.py
import os
import time
import hashlib
from fastapi import APIRouter, Depends, HTTPException

# auth.py থেকে verify_worker ইমপোর্ট করা হলো
from app.api.auth import verify_worker

router = APIRouter(prefix="/api/v1/cloudinary")

# os.environ এর বদলে os.getenv ব্যবহার করা হলো যেন ভেরিয়েবল না থাকলেও ক্র্যাশ না করে
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")

@router.post("/sign-upload")
async def generate_upload_signature(worker_id: str = Depends(verify_worker)):
    """Generates a secure upload signature for a Colab worker."""
    if not CLOUDINARY_API_SECRET:
        raise HTTPException(status_code=500, detail="Cloudinary secrets are not configured")

    timestamp = int(time.time())
    
    # Cloudinary requires alphabetical ordering of parameters for the signature
    folder = "distributed_platform_segments"
    signature_string = f"folder={folder}&timestamp={timestamp}{CLOUDINARY_API_SECRET}"
    
    signature = hashlib.sha1(signature_string.encode('utf-8')).hexdigest()
    
    return {
        "signature": signature,
        "timestamp": timestamp,
        "api_key": CLOUDINARY_API_KEY,
        "cloud_name": CLOUD_NAME,
        "folder": folder
    }
