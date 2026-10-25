# backend/app/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api import workers, tasks, jobs, cloudinary
from app.database import database  # Assuming databases async instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    # Start background task for lease recovery here
    yield
    await database.disconnect()

app = FastAPI(title="Distributed Video Processing API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
