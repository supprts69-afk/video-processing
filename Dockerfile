# Stage 1: Build the Next.js Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend

# npm প্যাকেজগুলো ইনস্টল করা
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# ফ্রন্টএন্ডের বাকি সব ফাইল কপি করা
COPY frontend/ ./

# Next.js স্ট্যাটিক বিল্ডের জন্য Supabase ভেরিয়েবলগুলো পাস করা
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY

# ফ্রন্টএন্ড বিল্ড করা (out/ ফোল্ডারে স্ট্যাটিক ফাইল তৈরি হবে)
RUN npm run build


# Stage 2: Build and Run the FastAPI Backend
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (ffmpeg and ffprobe required for finalization merges)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# পাইথন প্যাকেজ ইনস্টল করা
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ব্যাকএন্ডের কোড কপি করা
COPY backend/app ./app

# Stage 1 থেকে ফ্রন্টএন্ডের বিল্ড করা স্ট্যাটিক ফাইলগুলো কপি করা
COPY --from=frontend-builder /frontend/out /frontend/out

# Expose the port Render expects
EXPOSE 8000

# Run Uvicorn via shell to bind to Render's dynamic PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
