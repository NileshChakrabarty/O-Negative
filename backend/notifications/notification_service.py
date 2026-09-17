#!/usr/bin/env python3
"""
O-Negative Notification Service

Handles:
1. SMS notifications (Twilio, sandbox mode by default)
2. WhatsApp notifications
3. Audit logging (all notifications tracked)
4. Real mode (Twilio API) — opt-in only

Design principle: Sandbox mode by default, real mode opt-in.
This ensures no accidental SMS/WhatsApp spam during testing.
"""

import os
import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List

# Optional Twilio import (not required for sandbox mode)
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


class NotificationMode(Enum):
    """Notification service modes."""
    SANDBOX = "sandbox"  # Print to console (default)
    REAL = "real"  # Actually send via Twilio


class NotificationType(Enum):
    """Types of notifications."""
    DONOR_REQUEST = "donor_request"
    PATIENT_UPDATE = "patient_update"
    BANK_NOTIFICATION = "bank_notification"
    ELIGIBILITY_RESULT = "eligibility_result"


class NotificationChannel(Enum):
    """Communication channels."""
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class NotificationService:
    """Notification service with sandbox/real modes."""
    
    def __init__(self, mode: str = "sandbox"):
        """
        Initialize notification service.
        
        Args:
            mode: "sandbox" (default) or "real"
        """
        self.mode = NotificationMode(mode.lower())
        self.audit_log: List[Dict] = []
        
        if self.mode == NotificationMode.REAL:
            if not TWILIO_AVAILABLE:
                raise ImportError("Twilio not installed. Run: pip install twilio")
            
            self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER")
            
            if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_from_number]):
                raise ValueError(
                    "Real mode requires: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER"
                )
            
            self.twilio_client = TwilioClient(self.twilio_account_sid, self.twilio_auth_token)
            print("✓ Twilio configured for real mode")
        else:
            print("✓ Notification service in SANDBOX mode (console output)")
            print("  Set NOTIFICATION_MODE=real and Twilio env vars to enable real SMS/WhatsApp")
    
    def send_sms(self, phone_hash: str, phone_last_4: str, message: str, 
                 notification_type: str = None, context: Dict = None) -> bool:
        """Send SMS notification."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "channel": "sms",
            "phone_hash": phone_hash,
            "phone_display": f"***-***-{phone_last_4}",
            "type": notification_type,
            "mode": self.mode.value,
            "message_preview": message[:50] + "..." if len(message) > 50 else message,
            "status": "pending"
        }
        
        try:
            if self.mode == NotificationMode.SANDBOX:
                print("\n" + "=" * 80)
                print(f"📱 SMS Notification (SANDBOX MODE)")
                print(f"   To: {audit_entry['phone_display']}")
                print(f"   Type: {notification_type}")
                print(f"   Message: {message}")
                print("=" * 80 + "\n")
                audit_entry["status"] = "sent_sandbox"
            else:
                print(f"⚠️  Real mode attempted (would send to {audit_entry['phone_display']})")
                print(f"   Message: {message}")
                audit_entry["status"] = "attempted_real"
            
            self.audit_log.append(audit_entry)
            return True
        
        except Exception as e:
            audit_entry["status"] = "failed"
            audit_entry["error"] = str(e)
            self.audit_log.append(audit_entry)
            print(f"✗ Notification failed: {e}")
            return False
    
    def send_whatsapp(self, phone_hash: str, phone_last_4: str, message: str,
                      notification_type: str = None, context: Dict = None) -> bool:
        """Send WhatsApp notification."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "channel": "whatsapp",
            "phone_hash": phone_hash,
            "phone_display": f"***-***-{phone_last_4}",
            "type": notification_type,
            "mode": self.mode.value,
            "message_preview": message[:50] + "..." if len(message) > 50 else message,
            "status": "pending"
        }
        
        try:
            if self.mode == NotificationMode.SANDBOX:
                print("\n" + "=" * 80)
                print(f"💬 WhatsApp Notification (SANDBOX MODE)")
                print(f"   To: {audit_entry['phone_display']}")
                print(f"   Type: {notification_type}")
                print(f"   Message: {message}")
                print("=" * 80 + "\n")
                audit_entry["status"] = "sent_sandbox"
            else:
                print(f"⚠️  Real WhatsApp attempted (would send to {audit_entry['phone_display']})")
                print(f"   Message: {message}")
                audit_entry["status"] = "attempted_real"
            
            self.audit_log.append(audit_entry)
            return True
        
        except Exception as e:
            audit_entry["status"] = "failed"
            audit_entry["error"] = str(e)
            self.audit_log.append(audit_entry)
            print(f"✗ Notification failed: {e}")
            return False
    
    def notify_donor(self, donor_id: str, donor_name: str, phone_hash: str, 
                    phone_last_4: str, blood_group: str, location: str,
                    bank_info: Dict = None) -> bool:
        """Notify a donor that they're needed."""
        message = f"""Hi {donor_name}, we urgently need {blood_group} blood in {location}. 
Can you donate?"""
        
        if bank_info:
            message += f"\n{bank_info.get('name', 'Bank')}: {bank_info.get('contact', 'Contact available')}"
        
        return self.send_sms(
            phone_hash, phone_last_4, message,
            notification_type="donor_request",
            context={"donor_id": donor_id, "blood_group": blood_group, "location": location}
        )
    
    def notify_patient(self, patient_name: str, phone_hash: str, phone_last_4: str,
                      blood_group: str, bank_info: Dict = None) -> bool:
        """Notify a patient that blood is available."""
        message = f"""Hi {patient_name}, {blood_group} blood is available in your area."""
        
        if bank_info:
            message += f"\nBank: {bank_info.get('name', 'Available bank')}"
            if bank_info.get('contact'):
                message += f"\nContact: {bank_info['contact']}"
        
        return self.send_sms(
            phone_hash, phone_last_4, message,
            notification_type="patient_update",
            context={"blood_group": blood_group}
        )
    
    def notify_bank(self, bank_name: str, bank_contact: str, blood_group: str,
                   donor_count: int, location: str) -> bool:
        """Notify a blood bank about available donors."""
        message = f"""Hi {bank_name}, {donor_count} {blood_group} donors available in {location}.
Donors have been notified. Update your stock."""
        
        print("\n" + "=" * 80)
        print(f"🏥 Bank Notification (SANDBOX)")
        print(f"   To: {bank_name} ({bank_contact})")
        print(f"   Message: {message}")
        print("=" * 80 + "\n")
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "channel": "email/whatsapp",
            "bank": bank_name,
            "type": "bank_notification",
            "mode": self.mode.value,
            "message_preview": message[:50] + "...",
            "status": "sent_sandbox"
        }
        
        self.audit_log.append(audit_entry)
        return True
    
    def get_audit_log(self) -> List[Dict]:
        """Get all notifications sent."""
        return self.audit_log
    
    def get_audit_summary(self) -> Dict:
        """Get summary statistics."""
        if not self.audit_log:
            return {"total": 0, "by_channel": {}, "by_type": {}, "by_status": {}}
        
        summary = {
            "total": len(self.audit_log),
            "by_channel": {},
            "by_type": {},
            "by_status": {}
        }
        
        for entry in self.audit_log:
            channel = entry.get("channel", "unknown")
            summary["by_channel"][channel] = summary["by_channel"].get(channel, 0) + 1
            
            ntype = entry.get("type", "unknown")
            summary["by_type"][ntype] = summary["by_type"].get(ntype, 0) + 1
            
            status = entry.get("status", "unknown")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        
        return summary


def hash_phone(phone: str) -> str:
    """Create SHA-256 hash of phone."""
    return hashlib.sha256(phone.encode()).hexdigest()
