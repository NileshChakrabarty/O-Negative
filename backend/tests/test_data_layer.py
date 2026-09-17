#!/usr/bin/env python3
"""Tests for the data layer (blood banks + donor registry)."""

import sys
import os

# Ensure project root is on path for backend.* imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_blood_banks():
    """Test blood bank lookup."""
    from backend.data_layer.blood_banks import list_nearby_banks
    
    result = list_nearby_banks("Sonipat", radius_km=25)
    assert result["location"] == "Sonipat"
    assert result["count"] > 0
    assert len(result["banks"]) > 0
    
    bank = result["banks"][0]
    assert "bank_name" in bank
    assert "contact" in bank
    assert "distance_km" in bank
    print(f"✓ Blood bank lookup: found {result['count']} banks near Sonipat")
    for b in result["banks"]:
        print(f"  → {b['bank_name']} ({b['distance_km']:.1f} km)")


def test_donor_registry():
    """Test donor availability lookup."""
    from backend.data_layer.donor_registry import check_donor_availability
    
    result = check_donor_availability("O-", "Sonipat")
    assert result["blood_group"] == "O-"
    assert result["location"] == "Sonipat"
    print(f"✓ Donor registry: found {result['count']} O- donors in Sonipat")


if __name__ == "__main__":
    print("=" * 60)
    print("  Data Layer Tests")
    print("=" * 60)
    test_blood_banks()
    test_donor_registry()
    print("\n✓ All data layer tests passed!")
