#!/usr/bin/env python3
"""
Memory Database Manager

Handles:
1. Dual backend support: PostgreSQL (Supabase) + local SQLite fallback
2. Reading/writing donor history (memory that influences decisions)
3. Tracking blood bank reliability
4. Logging requests and outcomes
5. Ranking candidates by reliability score
"""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.config import DATABASE_URL, USE_SQLITE, MEMORY_DB_PATH


class MemoryDB:
    """Database for O-Negative's persistent memory (PostgreSQL or SQLite)."""
    
    def __init__(self, database_url: str = None, sqlite_path: str = None):
        """Initialize database connection (Postgres with SQLite fallback)."""
        self.database_url = database_url or DATABASE_URL
        self.sqlite_path = sqlite_path or MEMORY_DB_PATH
        self.backend = "sqlite"
        self.conn = None
        
        # Attempt PostgreSQL connection if URL provided and not forced to SQLite
        if self.database_url and not USE_SQLITE:
            try:
                import psycopg2
                self.conn = psycopg2.connect(self.database_url, connect_timeout=4)
                self.backend = "postgres"
                print("✓ Connected to PostgreSQL memory database")
            except Exception as e:
                print(f"⚠️ PostgreSQL connection failed ({e}). Falling back to local SQLite.")
                self.backend = "sqlite"
                self.conn = None

        if self.backend == "sqlite":
            self.conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._init_sqlite_schema()
            print(f"✓ Using SQLite memory database at {self.sqlite_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass

    def _init_sqlite_schema(self):
        """Initialize SQLite database with required schema."""
        cursor = self.conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS people (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT CHECK (role IN ('requester', 'donor', 'patient')),
            blood_group TEXT,
            phone_hash TEXT UNIQUE,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS donor_availability (
            person_id TEXT PRIMARY KEY REFERENCES people(id) ON DELETE CASCADE,
            availability_status TEXT CHECK (availability_status IN ('available', 'recently_donated', 'unavailable')),
            approx_location TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS donor_history (
            person_id TEXT PRIMARY KEY,
            last_donation_date DATE,
            recent_medication_flag BOOLEAN DEFAULT 0,
            recent_medication_note TEXT,
            response_count INTEGER DEFAULT 0,
            response_success_count INTEGER DEFAULT 0,
            avg_response_time_minutes INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS bank_reliability (
            bank_id TEXT PRIMARY KEY,
            bank_name TEXT,
            location TEXT,
            times_contact_successful INTEGER DEFAULT 0,
            times_contact_failed INTEGER DEFAULT 0,
            last_verified TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS requests (
            id TEXT PRIMARY KEY,
            requester_id TEXT,
            blood_group TEXT,
            location TEXT,
            raw_query TEXT,
            outcome TEXT,
            reasoning_trail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        """)
        self.conn.commit()
        cursor.close()

    def initialize(self):
        """Initialize full schema for current backend."""
        if self.backend == "sqlite":
            self._init_sqlite_schema()
        else:
            from backend.memory.schema import get_schema
            cursor = self.conn.cursor()
            cursor.execute(get_schema())
            self.conn.commit()
            cursor.close()
            print("✓ PostgreSQL schema initialized")

    # ========================================================================
    # People Management
    # ========================================================================

    def add_person(self, name: str, role: str, blood_group: str = None, 
                   phone_hash: str = None, location: str = None, person_id: str = None) -> str:
        """Add a person (donor, requester, or patient)."""
        pid = person_id or str(uuid.uuid4())
        try:
            cursor = self.conn.cursor()
            if self.backend == "postgres":
                cursor.execute("""
                    INSERT INTO people (id, name, role, blood_group, phone_hash, location)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        blood_group = EXCLUDED.blood_group,
                        location = EXCLUDED.location
                    RETURNING id
                """, (pid, name, role, blood_group, phone_hash, location))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO people (id, name, role, blood_group, phone_hash, location)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pid, name, role, blood_group, phone_hash, location))
            self.conn.commit()
            cursor.close()
            return pid
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"✗ Failed to add person: {e}")
            raise

    def get_person(self, person_id: str) -> Optional[Dict]:
        """Get person by ID."""
        try:
            cursor = self.conn.cursor()
            if self.backend == "postgres":
                from psycopg2.extras import RealDictCursor
                pcursor = self.conn.cursor(cursor_factory=RealDictCursor)
                pcursor.execute("SELECT * FROM people WHERE id = %s", (person_id,))
                row = pcursor.fetchone()
                pcursor.close()
                return dict(row) if row else None
            else:
                cursor.execute("SELECT * FROM people WHERE id = ?", (person_id,))
                row = cursor.fetchone()
                cursor.close()
                return dict(row) if row else None
        except Exception as e:
            print(f"✗ Failed to get person: {e}")
            return None

    # ========================================================================
    # Donor History & Reliability
    # ========================================================================

    def record_response(self, person_id: str, responded: bool, response_time_minutes: int = 15):
        """Record whether a donor responded to a request and how fast."""
        try:
            cursor = self.conn.cursor()
            history = self.get_donor_history(person_id) or {}
            response_count = history.get("response_count", 0) + 1
            response_success_count = history.get("response_success_count", 0) + (1 if responded else 0)
            
            avg_time = history.get("avg_response_time_minutes") or response_time_minutes
            if response_time_minutes:
                avg_time = int((avg_time * (response_count - 1) + response_time_minutes) / response_count)

            if self.backend == "postgres":
                cursor.execute("""
                    INSERT INTO donor_history (person_id, response_count, response_success_count, avg_response_time_minutes)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (person_id) DO UPDATE SET
                        response_count = EXCLUDED.response_count,
                        response_success_count = EXCLUDED.response_success_count,
                        avg_response_time_minutes = EXCLUDED.avg_response_time_minutes,
                        updated_at = now()
                """, (person_id, response_count, response_success_count, avg_time))
            else:
                cursor.execute("""
                    INSERT INTO donor_history (person_id, response_count, response_success_count, avg_response_time_minutes)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(person_id) DO UPDATE SET
                        response_count = excluded.response_count,
                        response_success_count = excluded.response_success_count,
                        avg_response_time_minutes = excluded.avg_response_time_minutes,
                        updated_at = CURRENT_TIMESTAMP
                """, (person_id, response_count, response_success_count, avg_time))

            self.conn.commit()
            cursor.close()
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"✗ Failed to record response: {e}")

    def get_donor_history(self, person_id: str) -> Optional[Dict]:
        """Get donor's historical record."""
        try:
            cursor = self.conn.cursor()
            if self.backend == "postgres":
                from psycopg2.extras import RealDictCursor
                pcursor = self.conn.cursor(cursor_factory=RealDictCursor)
                pcursor.execute("SELECT * FROM donor_history WHERE person_id = %s ORDER BY updated_at DESC LIMIT 1", (person_id,))
                row = pcursor.fetchone()
                pcursor.close()
                return dict(row) if row else None
            else:
                cursor.execute("SELECT * FROM donor_history WHERE person_id = ? ORDER BY updated_at DESC LIMIT 1", (person_id,))
                row = cursor.fetchone()
                cursor.close()
                return dict(row) if row else None
        except Exception as e:
            print(f"✗ Failed to get donor history: {e}")
            return None

    def get_donor_reliability(self, person_id: str) -> Dict[str, Any]:
        """Calculate a donor's reliability rate (0.0 - 1.0) and metrics."""
        history = self.get_donor_history(person_id)
        if not history:
            return {
                "person_id": person_id,
                "response_count": 0,
                "response_success_count": 0,
                "reliability_rate": 0.5,  # neutral default
                "avg_response_time_minutes": 30
            }
        
        count = history.get("response_count", 0)
        success = history.get("response_success_count", 0)
        rate = (success / count) if count > 0 else 0.5
        
        return {
            "person_id": person_id,
            "response_count": count,
            "response_success_count": success,
            "reliability_rate": round(rate, 2),
            "avg_response_time_minutes": history.get("avg_response_time_minutes", 30)
        }

    def rank_donors(self, donors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank candidate donors using persistent memory:
        Donors with higher response reliability and faster response times are ranked top.
        """
        if not donors:
            return []
        
        scored_donors = []
        for donor in donors:
            donor_id = donor.get("donor_id")
            reliability = self.get_donor_reliability(donor_id)
            enriched = dict(donor)
            enriched["reliability_rate"] = reliability["reliability_rate"]
            enriched["response_count"] = reliability["response_count"]
            enriched["avg_response_time"] = reliability["avg_response_time_minutes"]
            scored_donors.append(enriched)
            
        scored_donors.sort(key=lambda d: (d["reliability_rate"], -d["avg_response_time"]), reverse=True)
        return scored_donors

    # ========================================================================
    # Bank Reliability
    # ========================================================================

    def record_bank_contact(self, bank_id: str, bank_name: str, location: str, successful: bool):
        """Record success/failure of contacting a blood bank."""
        try:
            cursor = self.conn.cursor()
            if self.backend == "postgres":
                cursor.execute("""
                    INSERT INTO bank_reliability (bank_id, bank_name, location, times_contact_successful, times_contact_failed, last_verified)
                    VALUES (%s, %s, %s, %s, %s, now())
                    ON CONFLICT (bank_id) DO UPDATE SET
                        times_contact_successful = CASE WHEN %s THEN bank_reliability.times_contact_successful + 1 ELSE bank_reliability.times_contact_successful END,
                        times_contact_failed = CASE WHEN NOT %s THEN bank_reliability.times_contact_failed + 1 ELSE bank_reliability.times_contact_failed END,
                        last_verified = now()
                """, (bank_id, bank_name, location, 1 if successful else 0, 0 if successful else 1, successful, successful))
            else:
                cursor.execute("SELECT times_contact_successful, times_contact_failed FROM bank_reliability WHERE bank_id = ?", (bank_id,))
                row = cursor.fetchone()
                s_count = (row[0] if row else 0) + (1 if successful else 0)
                f_count = (row[1] if row else 0) + (0 if successful else 1)
                cursor.execute("""
                    INSERT INTO bank_reliability (bank_id, bank_name, location, times_contact_successful, times_contact_failed, last_verified)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(bank_id) DO UPDATE SET
                        times_contact_successful = excluded.times_contact_successful,
                        times_contact_failed = excluded.times_contact_failed,
                        last_verified = CURRENT_TIMESTAMP
                """, (bank_id, bank_name, location, s_count, f_count))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"✗ Failed to record bank contact: {e}")

    # ========================================================================
    # Request & Outcome Logging
    # ========================================================================

    def log_request(self, blood_group: str, location: str, raw_query: str, 
                    reasoning_trail: List[Dict] = None, requester_id: str = None) -> str:
        """Log a blood request and its reasoning trail."""
        request_id = str(uuid.uuid4())
        trail_json = json.dumps(reasoning_trail or [])
        try:
            cursor = self.conn.cursor()
            if self.backend == "postgres":
                cursor.execute("""
                    INSERT INTO requests (id, requester_id, blood_group, location, raw_query, outcome, reasoning_trail)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (request_id, requester_id, blood_group, location, raw_query, "processing", trail_json))
            else:
                cursor.execute("""
                    INSERT INTO requests (id, requester_id, blood_group, location, raw_query, outcome, reasoning_trail)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (request_id, requester_id, blood_group, location, raw_query, "processing", trail_json))
            self.conn.commit()
            cursor.close()
            return request_id
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"✗ Failed to log request: {e}")
            return request_id

    def update_request_outcome(self, request_id: str, outcome: str):
        """Update request outcome ('fulfilled', 'partial', 'unfulfilled')."""
        try:
            cursor = self.conn.cursor()
            if self.backend == "postgres":
                cursor.execute("""
                    UPDATE requests SET outcome = %s, completed_at = now() WHERE id = %s
                """, (outcome, request_id))
            else:
                cursor.execute("""
                    UPDATE requests SET outcome = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (outcome, request_id))
            self.conn.commit()
            cursor.close()
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"✗ Failed to update request outcome: {e}")

    # ========================================================================
    # Default Memory Seeder (for Demonstrating Load-Bearing Memory)
    # ========================================================================

    def seed_default_memory(self):
        """Seed memory history for standard demo donors."""
        # Donor Sonipat 001: 9 out of 10 success (90% reliability)
        self.add_person(name="Alice Sharma", role="donor", blood_group="O-", location="Sonipat", person_id="donor_sonipat_001")
        for _ in range(9):
            self.record_response("donor_sonipat_001", responded=True, response_time_minutes=10)
        self.record_response("donor_sonipat_001", responded=False, response_time_minutes=60)

        # Donor Sonipat 002: 4 out of 10 success (40% reliability)
        self.add_person(name="Bob Verma", role="donor", blood_group="O-", location="Sonipat", person_id="donor_sonipat_002")
        for _ in range(4):
            self.record_response("donor_sonipat_002", responded=True, response_time_minutes=45)
        for _ in range(6):
            self.record_response("donor_sonipat_002", responded=False, response_time_minutes=120)

        # Cousin: marked recently donated
        self.add_person(name="Rajiv Cousin", role="donor", blood_group="O+", location="Sonipat", person_id="donor_cousin_001")


# Global singleton instance
_memory_db_instance = None

def get_memory_db() -> MemoryDB:
    """Get or create singleton MemoryDB instance."""
    global _memory_db_instance
    if _memory_db_instance is None:
        _memory_db_instance = MemoryDB()
        _memory_db_instance.seed_default_memory()
    return _memory_db_instance
