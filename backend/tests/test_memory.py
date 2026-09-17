#!/usr/bin/env python3
"""Tests for the memory database."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_memory_db():
    """Test memory DB operations."""
    from backend.memory.memory_db import MemoryDB
    from backend.config import DATA_DIR
    
    test_db_path = str(DATA_DIR / "test_memory.db")
    db = MemoryDB(sqlite_path=test_db_path)
    
    # Test add person
    pid = db.add_person(name="Test Donor", role="donor", blood_group="O-", location="TestCity")
    assert pid is not None
    print(f"✓ Added person: {pid}")
    
    # Test get person
    person = db.get_person(pid)
    assert person is not None
    assert person["name"] == "Test Donor"
    print(f"✓ Retrieved person: {person['name']}")
    
    # Test record response
    db.record_response(pid, responded=True, response_time_minutes=10)
    db.record_response(pid, responded=True, response_time_minutes=15)
    db.record_response(pid, responded=False, response_time_minutes=60)
    print("✓ Recorded 3 responses")
    
    # Test reliability
    reliability = db.get_donor_reliability(pid)
    assert reliability["response_count"] == 3
    assert reliability["response_success_count"] == 2
    expected_rate = round(2/3, 2)
    assert reliability["reliability_rate"] == expected_rate
    print(f"✓ Reliability: {reliability['reliability_rate']*100:.0f}% ({reliability['response_count']} responses)")
    
    # Test log request
    req_id = db.log_request("O-", "TestCity", "Need O- blood urgently")
    assert req_id is not None
    print(f"✓ Logged request: {req_id}")
    
    # Cleanup
    db.close()
    os.remove(test_db_path)
    print("✓ Cleanup complete")


def test_memory_db_seed():
    """Test default memory seeding."""
    from backend.memory.memory_db import MemoryDB
    from backend.config import DATA_DIR
    
    test_db_path = str(DATA_DIR / "test_seed_memory.db")
    db = MemoryDB(sqlite_path=test_db_path)
    db.seed_default_memory()
    
    # Check Alice (90% reliability)
    alice_rel = db.get_donor_reliability("donor_sonipat_001")
    assert alice_rel["reliability_rate"] == 0.9
    print(f"✓ Alice Sharma reliability: {alice_rel['reliability_rate']*100:.0f}%")
    
    # Check Bob (40% reliability)
    bob_rel = db.get_donor_reliability("donor_sonipat_002")
    assert bob_rel["reliability_rate"] == 0.4
    print(f"✓ Bob Verma reliability: {bob_rel['reliability_rate']*100:.0f}%")
    
    # Test ranking
    donors = [
        {"donor_id": "donor_sonipat_001", "blood_group": "O-"},
        {"donor_id": "donor_sonipat_002", "blood_group": "O-"},
    ]
    ranked = db.rank_donors(donors)
    assert ranked[0]["donor_id"] == "donor_sonipat_001"  # Alice should be ranked first
    print(f"✓ Ranking: {ranked[0]['donor_id']} ranked first (highest reliability)")
    
    db.close()
    os.remove(test_db_path)


if __name__ == "__main__":
    print("=" * 60)
    print("  Memory Database Tests")
    print("=" * 60)
    test_memory_db()
    print()
    test_memory_db_seed()
    print("\n✓ All memory tests passed!")
