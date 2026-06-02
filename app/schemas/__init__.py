"""
Schémas Pydantic : valident les données entrantes et formatent les réponses de l'API.
Séparer les schémas des modèles SQL est une bonne pratique (sécurité + clarté du contrat API).
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field

from app.models import PlanType, SubStatus, UserRole


# ---------- Authentification ----------
class RegisterIn(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6)
    org_name: Optional[str] = None        # nom de la coopérative (sinon compte individuel)
    is_cooperative: bool = False


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Utilisateurs ----------
class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str]
    role: UserRole
    org_id: int

    class Config:
        from_attributes = True


class InviteMemberIn(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6)
    role: UserRole = UserRole.MEMBER


# ---------- Exploitations ----------
class FarmIn(BaseModel):
    name: str
    region: Optional[str] = None
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_ha: Optional[float] = None


class FarmOut(FarmIn):
    id: int
    org_id: int

    class Config:
        from_attributes = True


# ---------- Analyses ----------
class AnalysisIn(BaseModel):
    culture: str
    region: Optional[str] = None
    farm_id: Optional[int] = None
    measurements: Dict[str, float]        # {"pH":6.2,"Humidité":55,...}


class AnalysisOut(BaseModel):
    id: int
    culture: str
    region: Optional[str]
    score: Optional[int]
    verdict: Optional[str]
    advanced: bool
    measurements: Dict[str, Any]
    diagnostic: Optional[List[Dict[str, Any]]] = None   # détail par paramètre (calculé)
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Abonnements ----------
class SubscriptionOut(BaseModel):
    plan: PlanType
    status: SubStatus
    seats: int
    current_period_end: Optional[datetime]
    auto_renew: bool

    class Config:
        from_attributes = True


class ChangePlanIn(BaseModel):
    plan: PlanType
    seats: int = 1                        # nb de membres pour la coopérative


class UsageOut(BaseModel):
    period: str
    analyses_used: int
    analyses_limit: Optional[int]         # None = illimité
    history_days: Optional[int]           # None = illimité
    plan: PlanType


# ---------- Interprétation de fertilité (analyse de laboratoire) ----------
class FertiliteIn(BaseModel):
    ph: Optional[float] = None
    ce: Optional[float] = None
    ce_unite: str = "dS/m"                # "dS/m" ou "µS/cm"
    azote: Optional[float] = None         # N total, en %
    phosphore: Optional[float] = None     # P assimilable, en mg/kg
    potassium: Optional[float] = None     # K échangeable, en mg/kg
    matiere_organique: Optional[float] = None   # MO, en %
    texture: Optional[str] = None         # sableux | sablo-limoneux | limoneux | …
    farm_id: Optional[int] = None         # rattacher à une exploitation (optionnel)
