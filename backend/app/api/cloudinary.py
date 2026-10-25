# backend/app/api/cloudinary.py
import os
import time
import hashlib
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/v1/cloudinary")

CLOUDINARY_API_SECRET = os.environ["CLOUDINARY_API_SECRET"]
CLOUDINARY_API_KEY = os.environ["CLOUDINARY_API_KEY"]
CLOUD_NAME = os.environ["CLOUDINARY_CLOUD_NAME"]

@router.post("/sign-upload")
async def generate_upload_signature(worker=Depends(verify_worker_token)):
    """Generates a secure upload signature for a Colab worker."""
    timestamp = int(time.time())
    
    # Cloudinary requires alphabetical ordering of parameters for the signature
    # We restrict the upload to a specific folder to maintain organization
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
