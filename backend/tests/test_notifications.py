#!/usr/bin/env python3
"""Tests for the notification service."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_notification_service():
    """Test sandbox notification dispatch."""
    from backend.notifications.notification_service import NotificationService, hash_phone
    
    service = NotificationService(mode="sandbox")
    
    # Test donor notification
    success = service.notify_donor(
        donor_id="test_donor_001",
        donor_name="Test Donor",
        phone_hash=hash_phone("9876543210"),
        phone_last_4="3210",
        blood_group="O-",
        location="TestCity",
        bank_info={"name": "Test Bank", "contact": "123-456"}
    )
    assert success is True
    print("✓ Donor notification sent (sandbox)")
    
    # Test patient notification
    success = service.notify_patient(
        patient_name="Test Patient",
        phone_hash=hash_phone("9123456789"),
        phone_last_4="6789",
        blood_group="AB+",
        bank_info={"name": "Test Bank", "contact": "123-456"}
    )
    assert success is True
    print("✓ Patient notification sent (sandbox)")
    
    # Test audit log
    log = service.get_audit_log()
    assert len(log) == 2
    print(f"✓ Audit log: {len(log)} entries")
    
    # Test audit summary
    summary = service.get_audit_summary()
    assert summary["total"] == 2
    print(f"✓ Audit summary: {summary}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Notification Service Tests")
    print("=" * 60)
    test_notification_service()
    print("\n✓ All notification tests passed!")
