"""
Modèle OTPRecord — stockage sécurisé des codes OTP SMS.

Chaque demande OTP crée un enregistrement distinct.
L'OTP n'est JAMAIS stocké en clair : uniquement son HMAC-SHA256.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index

from app.core.database import Base


def _now_utc():
    return datetime.now(timezone.utc)


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, index=True)

    # Numéro de téléphone normalisé E.164 (+221XXXXXXXXX)
    phone = Column(String(20), nullable=False)

    # HMAC-SHA256 de l'OTP — jamais en clair
    otp_hash = Column(String(64), nullable=False)

    # Objectif : "login" | "reset_password" | "register"
    purpose = Column(String(32), nullable=False)

    # Expiration (5 minutes)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Compteur de tentatives incorrectes (max 5)
    attempts = Column(Integer, default=0, nullable=False)

    # Marqué True après vérification réussie (invalide immédiatement l'OTP)
    verified = Column(Boolean, default=False, nullable=False)

    # Marqué True si invalidé manuellement (nouvelle demande → invalide les anciens)
    invalidated = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=_now_utc, nullable=False)

    # Lien optionnel vers l'utilisateur (null pour register avant création compte)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Index composite pour les lookups fréquents
    __table_args__ = (
        Index("ix_otp_phone_purpose", "phone", "purpose"),
    )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_usable(self) -> bool:
        return (
            not self.verified
            and not self.invalidated
            and not self.is_expired
            and self.attempts < 5
        )
