# backend/app/api/auth.py
import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db_connection

ADMIN_API_SECRET = os.environ["ADMIN_API_SECRET"]

admin_scheme = APIKeyHeader(name="X-Admin-Secret")
worker_scheme = HTTPBearer()

async def verify_admin(api_key: str = Security(admin_scheme)):
    """Secures administrative endpoints."""
    if api_key != ADMIN_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid admin credentials"
        )
    return True

async def verify_worker(credentials: HTTPAuthorizationCredentials = Security(worker_scheme), db=Depends(get_db_connection)):
    """Verifies a worker's scoped token and retrieves their ID."""
    token = credentials.credentials
    # In production, securely hash the incoming token and compare it with the DB
    import hashlib
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    query = "SELECT id, status FROM workers WHERE api_token_hash = :hash"
    worker = await db.fetch_one(query, {"hash": token_hash})
    
    if not worker:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid worker token")
    if worker["status"] == "error" or worker["status"] == "offline":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Worker is disabled or offline")
        
    return str(worker["id"])
