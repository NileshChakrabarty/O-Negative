# O-Negative — Deployment & Production Guide

This guide covers deploying the O-Negative AI-driven blood coordination system to production environments.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                        User Browser                      │
│                  (Vercel Frontend: Next.js)              │
└─────────────────────────┬────────────────────────────────┘
                          │ HTTPS / JSON
                          ▼
┌──────────────────────────────────────────────────────────┐
│                 Backend API (Render / Railway)           │
│                 FastAPI Server: backend/main.py          │
│                                                          │
│    Orchestrator (backend/agent/)                         │
│         ↓                                                │
│    Live Data (backend/data_layer/)                       │
│    RAG Engine (backend/knowledge/)                       │
│    Persistent Memory (backend/memory/)                   │
│         ↓                                                │
│    data.gov.in / ChromaDB / PostgreSQL (Supabase)        │
└──────────────────────────────────────────────────────────┘
```

---

## 1. Backend Deployment (Render.com)

O-Negative includes pre-configured [render.yaml](file:///Users/nileshchakrabarty/Desktop/Rakt_Setu/render.yaml) and [Procfile](file:///Users/nileshchakrabarty/Desktop/Rakt_Setu/Procfile) for seamless deployment.

### Steps:
1. Push your repository to GitHub.
2. In Render dashboard, click **New +** → **Blueprint**.
3. Select your repository. Render will automatically detect `render.yaml`.
4. Configure the following environment variables in Render:
   - `GEMINI_API_KEY`: Your Google Gemini API Key
   - `DATABASE_URL`: Your Supabase connection string or PostgreSQL URL
   - `DATA_GOV_IN_API_KEY`: Your data.gov.in API key
   - `GOOGLE_MAPS_API_KEY`: Your Google Maps API key
   - `NOTIFICATION_MODE`: `sandbox` (or `real` if using Twilio)
5. Click **Apply**. Your backend will build using `pip install -r requirements.txt` and start with:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

---

## 2. Frontend Deployment (Vercel)

The `frontend/` directory is an optimized Next.js 14 project ready for Vercel.

### Steps:
1. In Vercel dashboard, click **Add New** → **Project**.
2. Import your GitHub repository.
3. Set **Root Directory** to `frontend`.
4. In **Environment Variables**, add:
   ```ini
   NEXT_PUBLIC_API_URL=https://your-backend-service.onrender.com
   ```
5. Click **Deploy**. Vercel will build and assign your production domain.

---

## 3. Database Setup (Supabase PostgreSQL)

1. Create a free project at [supabase.com](https://supabase.com).
2. Copy your connection URI from **Project Settings** → **Database** → **Connection String** (URI).
3. Set `DATABASE_URL` in your environment:
   ```ini
   DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres"
   ```
4. If connecting from environments without direct IPv4 support, O-Negative will automatically fall back to its robust local SQLite storage with zero downtime.

---

## 4. Production Health Verification

Once deployed, verify your services:

```bash
# Check backend health
curl https://your-backend-service.onrender.com/health

# Check system components
curl https://your-backend-service.onrender.com/api/system/status
```

Expected response:
```json
{
  "status": "healthy",
  "rag_rules_loaded": 34,
  "memory_backend": "sqlite",
  "gemini_active": true,
  "notification_mode": "sandbox"
}
```
