#!/usr/bin/env python3
"""
Donor Registry — Local Donor Availability Database

Manages the local SQLite database of donor availability status.
This is the operational read layer (Phase 1); historical memory
lives in backend.memory (Phase 3).
"""

import sqlite3
import os
from datetime import datetime, timedelta

from backend.config import DONOR_DB_PATH


def get_donor_db_path() -> str:
    """Return the path to the donor availability database."""
    return DONOR_DB_PATH


def init_database():
    """Initialize SQLite database with donor availability schema."""
    conn = sqlite3.connect(DONOR_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donor_availability (
            donor_id TEXT PRIMARY KEY,
            blood_group TEXT NOT NULL,
            approx_location TEXT NOT NULL,
            availability_status TEXT CHECK (availability_status IN ('available', 'recently_donated', 'unavailable')),
            last_status_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def get_available_donors(blood_group: str, location: str, radius_km: float = 15) -> list:
    """
    Fetch available donors from local database.
    
    Args:
        blood_group: e.g., "O-", "B+", "AB"
        location: Location/area
        radius_km: Search radius (currently location-based, not geo-based)
    
    Returns:
        List of available donors matching blood group and location
    """
    try:
        conn = sqlite3.connect(DONOR_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT donor_id, blood_group, approx_location, availability_status, last_status_update
            FROM donor_availability
            WHERE blood_group = ? AND approx_location = ? AND availability_status = 'available'
            ORDER BY last_status_update DESC
        """, (blood_group, location))
        
        rows = cursor.fetchall()
        conn.close()
        
        donors = []
        for row in rows:
            donors.append({
                "donor_id": row[0],
                "blood_group": row[1],
                "approx_location": row[2],
                "availability_status": row[3],
                "last_status_update": row[4]
            })
        
        return donors
    
    except Exception as e:
        print(f"Error fetching from donor DB: {e}")
        return []


def check_donor_availability(blood_group: str, location: str, radius_km: float = 15) -> dict:
    """
    Get currently available donors.
    
    Args:
        blood_group: Blood type (e.g., "O-", "AB+")
        location: Area/locality
        radius_km: Search radius in km (default 15)
    
    Returns:
        {
            "blood_group": str,
            "location": str,
            "radius_km": float,
            "count": int,
            "donors": list of {donor_id, blood_group, approx_location, availability_status, last_status_update}
        }
    """
    donors = get_available_donors(blood_group, location, radius_km)
    
    return {
        "blood_group": blood_group,
        "location": location,
        "radius_km": radius_km,
        "count": len(donors),
        "donors": donors
    }
