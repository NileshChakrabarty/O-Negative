#!/usr/bin/env python3
"""
Seed donor availability database with test data for demo.
"""

import sqlite3
import os
from datetime import datetime, timedelta

from backend.config import DONOR_DB_PATH


def seed_donor_availability():
    """Populate donor_availability table with realistic test data."""
    
    # Remove old DB to start fresh
    if os.path.exists(DONOR_DB_PATH):
        os.remove(DONOR_DB_PATH)
    
    conn = sqlite3.connect(DONOR_DB_PATH)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donor_availability (
            donor_id TEXT PRIMARY KEY,
            blood_group TEXT NOT NULL,
            approx_location TEXT NOT NULL,
            availability_status TEXT CHECK (availability_status IN ('available', 'recently_donated', 'unavailable')),
            last_status_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Sample test data: donors in Sonipat area with various blood groups and statuses
    now = datetime.now()
    test_donors = [
        # Available donors in Sonipat (O-, O+, B+, AB)
        ("donor_sonipat_001", "O-", "Sonipat", "available", now.isoformat()),
        ("donor_sonipat_002", "O-", "Sonipat", "available", (now - timedelta(hours=2)).isoformat()),
        ("donor_sonipat_003", "O+", "Sonipat", "available", (now - timedelta(hours=1)).isoformat()),
        ("donor_sonipat_004", "B+", "Sonipat", "available", (now - timedelta(minutes=30)).isoformat()),
        ("donor_sonipat_005", "AB+", "Sonipat", "available", now.isoformat()),
        
        # Recently donated (not available)
        ("donor_sonipat_006", "O-", "Sonipat", "recently_donated", (now - timedelta(days=10)).isoformat()),
        ("donor_sonipat_007", "O+", "Sonipat", "recently_donated", (now - timedelta(days=5)).isoformat()),
        
        # Unavailable
        ("donor_sonipat_008", "B-", "Sonipat", "unavailable", now.isoformat()),
        ("donor_sonipat_009", "AB-", "Sonipat", "unavailable", now.isoformat()),
        
        # Available donors in nearby Panipat
        ("donor_panipat_001", "O-", "Panipat", "available", (now - timedelta(hours=4)).isoformat()),
        ("donor_panipat_002", "A+", "Panipat", "available", (now - timedelta(hours=3)).isoformat()),
        
        # Demonstrate cousin scenario from spec
        ("donor_cousin_001", "O+", "Sonipat", "recently_donated", (now - timedelta(days=30)).isoformat()),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO donor_availability 
        (donor_id, blood_group, approx_location, availability_status, last_status_update)
        VALUES (?, ?, ?, ?, ?)
    """, test_donors)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Seeded {len(test_donors)} test donors in {DONOR_DB_PATH}")
    for donor_id, blood_group, location, status, _ in test_donors[:5]:
        print(f"  - {donor_id} ({blood_group}) in {location}: {status}")


if __name__ == "__main__":
    seed_donor_availability()
