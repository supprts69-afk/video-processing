# backend/app/api/auth.py
import os
# এখানে Depends যুক্ত করা হয়েছে
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db_connection

# os.environ এর বদলে os.getenv ব্যবহার করা হয়েছে যেন ভেরিয়েবল না থাকলেও ক্র্যাশ না করে
ADMIN_API_SECRET = os.getenv("ADMIN_API_SECRET", "")

admin_scheme = APIKeyHeader(name="X-Admin-Secret")
worker_scheme = HTTPBearer()

async def verify_admin(api_key: str = Security(admin_scheme)):
    """Secures administrative endpoints."""
    if not ADMIN_API_SECRET or api_key != ADMIN_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid admin credentials"
        )
    return True

async def verify_worker(credentials: HTTPAuthorizationCredentials = Security(worker_scheme), db=Depends(get_db_connection)):
    """Verifies a worker's scoped token and retrieves their ID."""
    token = credentials.credentials
    import hashlib
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    query = "SELECT id, status FROM workers WHERE api_token_hash = :hash"
    worker = await db.fetch_one(query, {"hash": token_hash})
    
    if not worker:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid worker token")
    if worker["status"] == "error" or worker["status"] == "offline":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Worker is disabled or offline")
        
    return str(worker["id"])
