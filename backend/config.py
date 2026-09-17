#!/usr/bin/env python3
"""
O-Negative Centralized Configuration

Single source of truth for all environment variables, API keys,
database URLs, and service configuration. Loads .env once and
validates credentials at import time.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================================
# Load .env from project root (one time, globally)
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ============================================================================
# Data Directories
# ============================================================================

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DONOR_DB_PATH = str(DATA_DIR / "donor_availability.db")
MEMORY_DB_PATH = str(DATA_DIR / "o_negative_memory.db") if (DATA_DIR / "o_negative_memory.db").exists() else str(DATA_DIR / "rakt_setu_memory.db")
CHROMA_DB_PATH = str(DATA_DIR / ".chroma_data")

# ============================================================================
# LLM Configuration (Google Gemini)
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.6-flash"

# ============================================================================
# Database Configuration (Supabase PostgreSQL + SQLite fallback)
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_SQLITE = os.getenv("USE_SQLITE", "").lower() == "true" or not DATABASE_URL

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")

# ============================================================================
# External APIs
# ============================================================================

DATA_GOV_IN_API_KEY = os.getenv("DATA_GOV_IN_API_KEY", "")
DATA_GOV_API_BASE = "https://api.data.gov.in/resource"
BLOOD_BANK_DATASET_ID = "9ef6b007-4112-4513-8b40-4bcccfff5786"

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GOOGLE_DISTANCE_API_BASE = "https://maps.googleapis.com/maps/api/distancematrix/json"

# ============================================================================
# Notification Configuration
# ============================================================================

NOTIFICATION_MODE = os.getenv("NOTIFICATION_MODE", "sandbox")

# ============================================================================
# Server Configuration
# ============================================================================

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# ============================================================================
# Startup Validation & Status Report
# ============================================================================

def print_startup_status():
    """Print a clear status report of all credentials and services."""
    print("\n" + "=" * 70)
    print("  O-Negative — Startup Configuration Report")
    print("=" * 70)
    
    # Gemini
    if GEMINI_API_KEY:
        print(f"  ✓ Gemini API Key        : configured ({GEMINI_MODEL})")
    else:
        print(f"  ✗ Gemini API Key        : MISSING — will use deterministic fallback")
    
    # Database
    if DATABASE_URL and not USE_SQLITE:
        print(f"  ◎ Database              : PostgreSQL (attempting connection)")
    else:
        print(f"  ◎ Database              : SQLite (local at {MEMORY_DB_PATH})")
    
    # External APIs
    if DATA_GOV_IN_API_KEY:
        print(f"  ✓ data.gov.in API Key   : configured")
    else:
        print(f"  ⚠ data.gov.in API Key   : MISSING — using local bank directory")
    
    if GOOGLE_MAPS_API_KEY:
        print(f"  ✓ Google Maps API Key   : configured")
    else:
        print(f"  ⚠ Google Maps API Key   : MISSING — using preset distances")
    
    # Notifications
    print(f"  ◎ Notification Mode     : {NOTIFICATION_MODE}")
    
    # Server
    print(f"  ◎ Server                : {HOST}:{PORT}")
    
    print("=" * 70 + "\n")
