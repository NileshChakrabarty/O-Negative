"""Donor routes — roster, toggle availability, reliability enrichment."""

import sqlite3
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config import DONOR_DB_PATH
from backend.memory.memory_db import get_memory_db

router = APIRouter()


class DonorToggleRequest(BaseModel):
    donor_id: str
    status: Optional[str] = None  # 'available' or 'unavailable'


@router.get("/api/donors")
async def get_donors(blood_group: Optional[str] = None, location: str = "Sonipat"):
    """Get active donor roster with historical reliability scores."""
    try:
        conn = sqlite3.connect(DONOR_DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        if blood_group:
            cur.execute("""
                SELECT donor_id, blood_group, approx_location, availability_status, last_status_update
                FROM donor_availability
                WHERE approx_location = ? AND blood_group = ?
                ORDER BY availability_status ASC, last_status_update DESC
            """, (location, blood_group))
        else:
            cur.execute("""
                SELECT donor_id, blood_group, approx_location, availability_status, last_status_update
                FROM donor_availability
                WHERE approx_location = ?
                ORDER BY availability_status ASC, last_status_update DESC
            """, (location,))
            
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        
        # Enrich with memory reliability
        memory_db = get_memory_db()
        if memory_db:
            for d in rows:
                rel = memory_db.get_donor_reliability(d["donor_id"])
                d["reliability_rate"] = rel["reliability_rate"]
                d["response_count"] = rel["response_count"]
                d["avg_response_time"] = rel["avg_response_time_minutes"]
                
        return {"count": len(rows), "donors": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Donor query error: {str(e)}")


@router.post("/api/donors/toggle")
async def toggle_donor_status(req: DonorToggleRequest):
    """Toggle a donor's availability between available and unavailable."""
    try:
        conn = sqlite3.connect(DONOR_DB_PATH)
        cur = conn.cursor()
        
        if req.status:
            new_status = req.status
        else:
            cur.execute("SELECT availability_status FROM donor_availability WHERE donor_id = ?", (req.donor_id,))
            row = cur.fetchone()
            current = row[0] if row else "available"
            new_status = "unavailable" if current == "available" else "available"
            
        cur.execute("""
            UPDATE donor_availability 
            SET availability_status = ?, last_status_update = CURRENT_TIMESTAMP
            WHERE donor_id = ?
        """, (new_status, req.donor_id))
        conn.commit()
        conn.close()
        
        return {"donor_id": req.donor_id, "new_status": new_status, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle donor: {str(e)}")
