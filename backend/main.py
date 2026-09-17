#!/usr/bin/env python3
"""
O-Negative API — Main Entry Point

Serves the Next.js coordination dashboard by wrapping:
- Agent Orchestrator (with Gemini 3.6 Flash & RAG)
- Live Data Layer (Blood banks & donor registry)
- Persistent Memory (Reliability scoring & audit logging)
- Notification Service (Sandbox / Twilio)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import PORT, HOST, print_startup_status

# Import route modules
from backend.api.routes_system import router as system_router
from backend.api.routes_query import router as query_router
from backend.api.routes_donors import router as donors_router
from backend.api.routes_banks import router as banks_router
from backend.api.routes_notifications import router as notifications_router

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="O-Negative API",
    version="1.0.0",
    description="AI-driven Blood Coordination System for India"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route modules
app.include_router(system_router)
app.include_router(query_router)
app.include_router(donors_router)
app.include_router(banks_router)
app.include_router(notifications_router)


# ============================================================================
# Startup
# ============================================================================

@app.on_event("startup")
async def on_startup():
    """Ensure data directory and seed data exist at startup."""
    from backend.data_layer.seed_data import seed_donor_availability
    from backend.config import DONOR_DB_PATH, DATA_DIR
    
    DATA_DIR.mkdir(exist_ok=True)
    
    # Seed donor DB if it doesn't exist
    if not os.path.exists(DONOR_DB_PATH):
        seed_donor_availability()


if __name__ == "__main__":
    import uvicorn
    
    print_startup_status()
    
    print(f"🚀 O-Negative API starting on http://localhost:{PORT}")
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=True,
        reload_dirs=["backend"]
    )
