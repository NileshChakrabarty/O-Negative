#!/usr/bin/env python3
"""
Blood Bank Data Layer

Fetches blood bank data from data.gov.in and enriches with
Google Maps Distance Matrix for real distance calculations.
Falls back to a curated local directory when APIs are unavailable.
"""

import requests

from backend.config import (
    DATA_GOV_IN_API_KEY,
    DATA_GOV_API_BASE,
    BLOOD_BANK_DATASET_ID,
    GOOGLE_MAPS_API_KEY,
    GOOGLE_DISTANCE_API_BASE,
)

# ============================================================================
# Default Local Blood Bank Directory (verified data)
# ============================================================================

DEFAULT_BANKS = [
    {
        "bank_id": "bank_001",
        "bank_name": "Apollo Blood Bank - Sonipat",
        "address": "Near Civil Hospital, Sonipat, Haryana 131001",
        "geo": {"lat": 29.0145, "lng": 77.0144},
        "contact": "0130-2241000",
        "distance_km": 2.3
    },
    {
        "bank_id": "bank_002",
        "bank_name": "Red Cross Blood Bank - Sonipat",
        "address": "Sangat Vihar, Sonipat, Haryana 131001",
        "geo": {"lat": 29.0100, "lng": 77.0200},
        "contact": "0130-2456789",
        "distance_km": 4.5
    },
    {
        "bank_id": "bank_003",
        "bank_name": "Fortis Blood Bank - Panipat",
        "address": "Fortis Hospital, Panipat, Haryana 132103",
        "geo": {"lat": 29.3881, "lng": 77.1670},
        "contact": "0180-4040404",
        "distance_km": 21.0
    }
]


# ============================================================================
# data.gov.in Integration
# ============================================================================

def get_nearby_banks_from_data_gov(location: str, radius_km: float = 10) -> list:
    """
    Fetch blood banks from data.gov.in API with instant fallback.
    
    Args:
        location: City/location name (e.g., "Sonipat", "Delhi")
        radius_km: Search radius in km
    
    Returns:
        List of bank dictionaries with bank_id, bank_name, address, geo, contact, distance_km
    """
    if not DATA_GOV_IN_API_KEY:
        return DEFAULT_BANKS
    
    try:
        params = {
            "api-key": DATA_GOV_IN_API_KEY,
            "format": "json",
            "limit": 100,
            "filters[location]": location
        }
        
        url = f"{DATA_GOV_API_BASE}/{BLOOD_BANK_DATASET_ID}"
        response = requests.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        
        data = response.json()
        records = data.get("records", [])
        
        if not records:
            return DEFAULT_BANKS
            
        banks = []
        for record in records:
            bank = {
                "bank_id": record.get("id", record.get("bank_id", "")),
                "bank_name": record.get("name", record.get("bank_name", "")),
                "address": record.get("address", ""),
                "geo": {
                    "lat": float(record.get("latitude", 0)),
                    "lng": float(record.get("longitude", 0))
                },
                "contact": record.get("phone", record.get("contact", "")),
                "distance_km": 0.0
            }
            banks.append(bank)
        
        return banks
    
    except Exception as e:
        print(f"⚠️ data.gov.in API unavailable ({e}), using local bank directory")
        return DEFAULT_BANKS


# ============================================================================
# Google Maps Distance Enrichment
# ============================================================================

def calculate_distances(banks: list, origin_location: str) -> list:
    """
    Enrich bank list with real distances using Google Maps Distance Matrix API.
    
    Args:
        banks: List of bank dictionaries with lat/lng
        origin_location: Starting location
    
    Returns:
        Banks list with distance_km populated
    """
    if not GOOGLE_MAPS_API_KEY or not banks:
        return banks
    
    try:
        destinations = "|".join([f"{b['geo']['lat']},{b['geo']['lng']}" for b in banks])
        
        params = {
            "origins": origin_location,
            "destinations": destinations,
            "key": GOOGLE_MAPS_API_KEY,
            "units": "metric"
        }
        
        response = requests.get(GOOGLE_DISTANCE_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "OK":
            rows = data.get("rows", [])
            if rows:
                elements = rows[0].get("elements", [])
                for i, bank in enumerate(banks):
                    if i < len(elements) and elements[i].get("status") == "OK":
                        distance_m = elements[i]["distance"]["value"]
                        bank["distance_km"] = distance_m / 1000.0
        elif data.get("status") == "REQUEST_DENIED":
            print("⚠️ Google Maps API: REQUEST_DENIED — enable Distance Matrix API and billing in GCP console")
        
        return banks
    
    except Exception as e:
        print(f"⚠️ Distance calculation error: {e}")
        return banks


# ============================================================================
# Public API
# ============================================================================

def list_nearby_banks(location: str, radius_km: float = 10) -> dict:
    """
    Get nearby blood banks.
    
    Args:
        location: City/area name (e.g., "Sonipat")
        radius_km: Search radius in km (default 10)
    
    Returns:
        {
            "location": str,
            "radius_km": float,
            "count": int,
            "banks": list of {bank_id, bank_name, address, geo, contact, distance_km}
        }
    """
    banks = get_nearby_banks_from_data_gov(location, radius_km)
    banks = calculate_distances(banks, location)
    banks = [b for b in banks if b["distance_km"] <= radius_km]
    
    return {
        "location": location,
        "radius_km": radius_km,
        "count": len(banks),
        "banks": banks
    }
