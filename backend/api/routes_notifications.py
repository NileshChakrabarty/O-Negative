"""Notification routes — dispatch and audit log."""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config import NOTIFICATION_MODE
from backend.notifications.notification_service import NotificationService, hash_phone

router = APIRouter()

# Shared instance
_notification_service = None

def _get_service() -> NotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(mode=NOTIFICATION_MODE)
    return _notification_service


class NotificationRequest(BaseModel):
    recipient_type: str  # 'donor', 'patient', 'bank'
    recipient_id: str
    recipient_name: str
    phone_last_4: str = "3210"
    blood_group: Optional[str] = "O-"
    location: Optional[str] = "Sonipat"
    bank_info: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    success: bool
    status: str
    audit_entry: Optional[Dict[str, Any]] = None


@router.post("/api/notify", response_model=NotificationResponse)
async def send_notification(request: NotificationRequest):
    """Dispatch blood coordination notification (sandbox or real Twilio SMS)."""
    try:
        service = _get_service()
        success = False
        
        if request.recipient_type == "donor":
            success = service.notify_donor(
                donor_id=request.recipient_id,
                donor_name=request.recipient_name,
                phone_hash=hash_phone(f"***{request.phone_last_4}"),
                phone_last_4=request.phone_last_4,
                blood_group=request.blood_group or "O-",
                location=request.location or "Sonipat",
                bank_info=request.bank_info
            )
        elif request.recipient_type == "patient":
            success = service.notify_patient(
                patient_name=request.recipient_name,
                phone_hash=hash_phone(f"***{request.phone_last_4}"),
                phone_last_4=request.phone_last_4,
                blood_group=request.blood_group or "O-",
                bank_info=request.bank_info
            )
        elif request.recipient_type == "bank":
            success = service.notify_bank(
                bank_name=request.recipient_name,
                bank_contact=request.bank_info.get("contact", "") if request.bank_info else "",
                blood_group=request.blood_group or "O-",
                donor_count=request.bank_info.get("donor_count", 1) if request.bank_info else 1,
                location=request.location or "Sonipat"
            )
        
        audit_log = service.get_audit_log()
        audit_entry = audit_log[-1] if audit_log else None
        
        return NotificationResponse(
            success=success,
            status="sent" if success else "failed",
            audit_entry=audit_entry
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification error: {str(e)}")


@router.get("/api/notifications/audit")
async def get_audit_log():
    """Get full audit log of all notifications dispatched."""
    service = _get_service()
    return {
        "total": len(service.get_audit_log()),
        "summary": service.get_audit_summary(),
        "entries": service.get_audit_log()
    }
