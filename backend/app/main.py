import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import workers, tasks, jobs, cloudinary
from app.database import database

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    # Start background task for lease recovery here
    yield
    await database.disconnect()

app = FastAPI(title="Distributed Video Processing API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since frontend and backend are on the same domain now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(workers.router)
app.include_router(tasks.router)
app.include_router(jobs.router)
app.include_router(cloudinary.router)

@app.get("/health")
async def health_check():
    """Liveness probe for Render."""
    return {"status": "ok"}

@app.get("/ready")
async def readiness_check():
    """Readiness probe checking DB connection."""
    try:
        await database.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable")

# ==========================================
# Next.js Frontend Serving Logic
# ==========================================
frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend/out")

if os.path.isdir(frontend_path):
    # Next.js এর _next ফোল্ডার সার্ভ করা
    app.mount("/_next", StaticFiles(directory=f"{frontend_path}/_next"), name="next-static")
    
    # বাকি সব রিকোয়েস্টের জন্য index.html সার্ভ করা (SPA Routing-এর জন্য)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))
