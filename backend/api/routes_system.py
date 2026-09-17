"""System & health check routes."""

from fastapi import APIRouter
from backend.agent.orchestrator import gemini_client
from backend.config import GEMINI_MODEL
from backend.api.routes_notifications import _get_service

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "O-Negative API", "version": "1.0.0"}


@router.get("/api/system/status")
async def system_status():
    """Return health and telemetry across all system layers."""
    from backend.memory.memory_db import get_memory_db
    
    memory_db = get_memory_db()
    notification_service = _get_service()
    
    return {
        "status": "ready",
        "llm_engine": f"{GEMINI_MODEL}" if gemini_client else "Deterministic Clinical Rules",
        "llm_active": gemini_client is not None,
        "rag_status": "Active (ChromaDB Vector Store)",
        "memory_backend": memory_db.backend if memory_db else "sqlite",
        "notification_mode": notification_service.mode.value,
        "notification_count": len(notification_service.get_audit_log()),
    }

