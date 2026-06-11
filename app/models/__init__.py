"""
Modèles de données (tables SQL) d'AgroScan Pro.

Architecture multi-tenant par "Organisation" :
- Un compte individuel = une organisation à 1 membre.
- Une coopérative = une organisation à plusieurs membres et plusieurs exploitations.
L'abonnement est porté par l'ORGANISATION, pas par l'utilisateur : c'est la bonne
pratique SaaS qui permet de facturer une équipe et de partager les quotas.

Tables :
  organizations   -> le "tenant" (client facturable)
  users           -> les comptes de connexion, rattachés à une organisation
  subscriptions   -> l'abonnement courant d'une organisation (plan + statut + dates)
  payments        -> historique des paiements (Wave / Orange Money / PayDunya)
  farms           -> exploitations / parcelles (utile surtout en coopérative)
  analyses        -> chaque diagnostic de sol enregistré
  usage_counters  -> compteur mensuel de consommation (pour les quotas du plan gratuit)
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Text, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def now_utc():
    return datetime.now(timezone.utc)


# --------- Énumérations ---------
class PlanType(str, enum.Enum):
    GRATUIT = "gratuit"
    PREMIUM = "premium"
    COOPERATIVE = "cooperative"


class SubStatus(str, enum.Enum):
    ACTIVE = "active"        # abonnement payé et en cours
    TRIAL = "trial"          # période d'essai
    PAST_DUE = "past_due"    # paiement en retard
    CANCELED = "canceled"    # résilié
    EXPIRED = "expired"      # échu


class UserRole(str, enum.Enum):
    OWNER = "owner"          # propriétaire de l'organisation (facturation)
    ADMIN = "admin"          # gère les membres et exploitations
    MEMBER = "member"        # technicien / agriculteur membre
    VIEWER = "viewer"        # lecture seule (ex : bailleur, ONG)


# --------- Tables ---------
class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    is_cooperative = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now_utc)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="organization",
                                uselist=False, cascade="all, delete-orphan")
    farms = relationship("Farm", back_populates="organization", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String)                       # numéro WhatsApp
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OWNER)
    profil = Column(String, nullable=False, default="producteur")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_utc)

    organization = relationship("Organization", back_populates="users")
    analyses = relationship("Analysis", back_populates="user")


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), unique=True, nullable=False)
    plan = Column(Enum(PlanType), default=PlanType.GRATUIT, nullable=False)
    status = Column(Enum(SubStatus), default=SubStatus.ACTIVE, nullable=False)
    started_at = Column(DateTime, default=now_utc)
    current_period_end = Column(DateTime)        # date d'échéance de la période payée
    seats = Column(Integer, default=1)           # nb de membres autorisés (coopérative)
    auto_renew = Column(Boolean, default=True)

    organization = relationship("Organization", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    provider = Column(String)                    # wave | orange_money | paydunya | manuel
    provider_ref = Column(String)                # référence de transaction du PSP
    amount_ht = Column(Integer)                  # montant hors taxe (FCFA)
    vat = Column(Integer)                        # TVA 18 % (FCFA)
    amount_ttc = Column(Integer)                 # montant TTC payé (FCFA)
    status = Column(String, default="pending")   # pending | paid | failed
    created_at = Column(DateTime, default=now_utc)

    subscription = relationship("Subscription", back_populates="payments")


class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)        # ex : "Parcelle Nord", "Champ de Modou"
    region = Column(String)                      # une des 14 régions du Sénégal
    locality = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    area_ha = Column(Float)                      # superficie en hectares
    created_at = Column(DateTime, default=now_utc)

    organization = relationship("Organization", back_populates="farms")
    analyses = relationship("Analysis", back_populates="farm")


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    farm_id = Column(Integer, ForeignKey("farms.id"))
    culture = Column(String)
    region = Column(String)
    # mesures brutes des 8 paramètres (JSON : {"pH":6.2,"Humidité":55,...})
    measurements = Column(JSON)
    score = Column(Integer)                      # nb de paramètres optimaux /8
    verdict = Column(String)                     # Excellent / Bon / Moyen / À corriger
    advanced = Column(Boolean, default=False)    # True si recommandations avancées (premium)
    created_at = Column(DateTime, default=now_utc)

    organization = relationship("Organization", back_populates="analyses")
    user = relationship("User", back_populates="analyses")
    farm = relationship("Farm", back_populates="analyses")


class UsageCounter(Base):
    """Compteur de consommation par organisation et par mois (clé AAAA-MM)."""
    __tablename__ = "usage_counters"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    period = Column(String, index=True)          # ex : "2026-05"
    analyses_count = Column(Integer, default=0)


# Importer les modèles agronomiques pour que Base.metadata les découvre.
from app.models.agronomie import (  # noqa: F401, E402
    Culture, Variete, ParametreClimatique, BesoinEau, BesoinNutritionnel,
    StadePhenologique, CalendrierCultural, RendementReference,
    Maladie, CultureMaladie, Ravageur, CultureRavageur, RecommandationCulture,
)

# Module Mon Champ
from app.models.champ import (  # noqa: F401, E402
    Parcelle, Parcelle as ChampParcelle, Cartographie, AnalyseSol,
    Infrastructure, SourceEau,
)

# Module Santé des Cultures
from app.models.sante import (  # noqa: F401, E402
    Consultation, Observation, PhotoConsultation,
    Diagnostic, Traitement, Suivi, RapportSante,
)

# Module Gestion de Ferme
from app.models.ferme import (  # noqa: F401, E402
    Activite, Preuve, Cout, MainOeuvre, JournalEntree,
)

# Module Météo & Alertes Intelligentes
from app.models.meteo import (  # noqa: F401, E402
    ConditionMeteo, Prevision, Alerte, ConfigAlertes, RecommandationPlan,
)

# Module IA Agricole
from app.models.ia import (  # noqa: F401, E402
    Conversation, MessageIA, RecommandationIA, FeedbackIA, ConfigIA,
)

# Module Satellite — Sentinel Hub
from app.models.satellite import (  # noqa: F401, E402
    SatelliteProduct, SatelliteJob, SatelliteConfig, SatelliteMetrics,
    SensorType, JobStatus, JobType,
)
