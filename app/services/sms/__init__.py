"""SMS service — provider-agnostic OTP delivery."""
from app.services.sms.base import SMSProvider, SMSResult
from app.services.sms.factory import get_sms_provider, detect_provider_for_phone

__all__ = ["SMSProvider", "SMSResult", "get_sms_provider", "detect_provider_for_phone"]
