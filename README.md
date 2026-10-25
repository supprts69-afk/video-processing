# Distributed Video Processing Platform

A robust, distributed FFmpeg processing system leveraging Google Colab as ephemeral workers, orchestrated by a central Mother API, with durable queueing in Supabase.

## 1. Local Development Setup

1. **Clone & Install**:
   ```bash
   git clone <repo-url> && cd distributed-video-platform/backend
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
