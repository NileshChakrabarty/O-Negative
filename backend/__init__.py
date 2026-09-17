"""
O-Negative Backend — AI-driven Blood Coordination System for India.

Modules:
    data_layer  — Blood bank APIs (data.gov.in) & donor registry
    knowledge   — RAG engine & NBTC/NACO eligibility rules
    memory      — Persistent memory (PostgreSQL / SQLite)
    agent       — Gemini-powered orchestrator & reasoning pipeline
    notifications — SMS/WhatsApp dispatch (sandbox / Twilio)
    api         — FastAPI route handlers
"""

__version__ = "1.0.0"

