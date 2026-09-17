"""Blood bank routes — nearby bank lookup."""

from fastapi import APIRouter, HTTPException

from backend.data_layer.blood_banks import list_nearby_banks

router = APIRouter()


@router.get("/api/banks")
async def get_banks(location: str = "Sonipat", radius_km: float = 25.0):
    """Get verified nearby blood banks from data.gov.in registry."""
    try:
        data = list_nearby_banks(location, radius_km)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bank directory error: {str(e)}")
