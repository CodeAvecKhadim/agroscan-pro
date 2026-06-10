"""
Modèles SQLAlchemy — Module IA Agricole AgroScan.
Tables préfixe ia_ : conversations, messages, recommandations, feedback, config.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, SmallInteger, String, Float, Boolean,
    DateTime, ForeignKey, Enum, Text, ARRAY,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


# ── Enums ─────────────────────────────────────────────────────────────────────

class StatutConversation(str, enum.Enum):
    ACTIVE    = "active"
    ARCHIVEE  = "archivee"
    TERMINEE  = "terminee"


class ModeConversation(str, enum.Enum):
    LIBRE             = "libre"
    ANALYSE_PARCELLE  = "analyse_parcelle"
    DIAGNOSTIC        = "diagnostic"
    PLANIFICATION     = "planification"
    BILAN             = "bilan"


class RoleMessage(str, enum.Enum):
    USER      = "user"
    ASSISTANT = "assistant"
    SYSTEM    = "system"


class CategorieReco(str, enum.Enum):
    SOL           = "sol"
    FERTILISATION = "fertilisation"
    MALADIE       = "maladie"
    RAVAGEUR      = "ravageur"
    IRRIGATION    = "irrigation"
    CALENDRIER    = "calendrier"
    RECOLTE       = "recolte"
    GENERAL       = "general"


class StatutReco(str, enum.Enum):
    NOUVELLE  = "nouvelle"
    VUE       = "vue"
    APPLIQUEE = "appliquee"
    IGNOREE   = "ignoree"


class TonAssistant(str, enum.Enum):
    TECHNIQUE   = "technique"
    SIMPLE      = "simple"
    PEDAGOGIQUE = "pedagogique"


# ── Modèles ───────────────────────────────────────────────────────────────────

class Conversation(Base):
    """Session de conversation entre un utilisateur et l'IA agricole."""
    __tablename__ = "ia_conversations"

    id              = Column(Integer, primary_key=True)
    org_id          = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    parcelle_id     = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=True)
    culture_id      = Column(Integer, ForeignKey("agro_cultures.id"), nullable=True)
    titre           = Column(String(200))
    statut          = Column(Enum(StatutConversation), default=StatutConversation.ACTIVE, nullable=False)
    mode            = Column(Enum(ModeConversation), default=ModeConversation.LIBRE, nullable=False)
    nb_messages     = Column(Integer, default=0)
    tokens_total    = Column(Integer, default=0)
    contexte_init   = Column(JSONB)
    mois_periode    = Column(String(7))         # "2026-06" pour quota mensuel
    created_at      = Column(DateTime, default=_now)
    updated_at      = Column(DateTime, default=_now, onupdate=_now)

    messages          = relationship("MessageIA", back_populates="conversation",
                                     cascade="all, delete-orphan",
                                     order_by="MessageIA.created_at")
    recommandations   = relationship("RecommandationIA", back_populates="conversation",
                                     cascade="all, delete-orphan")
    feedbacks         = relationship("FeedbackIA", back_populates="conversation",
                                     cascade="all, delete-orphan")


class MessageIA(Base):
    """Message individuel dans une conversation (user ou assistant)."""
    __tablename__ = "ia_messages"

    id              = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("ia_conversations.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    org_id          = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    role            = Column(Enum(RoleMessage), nullable=False)
    contenu         = Column(Text, nullable=False)
    tokens_in       = Column(Integer)
    tokens_out      = Column(Integer)
    modele          = Column(String(60))
    duree_ms        = Column(Integer)
    contexte_inject = Column(JSONB)             # snapshot contexte agro (assistant only)
    regles_codes    = Column(ARRAY(String))     # codes règles utilisées
    created_at      = Column(DateTime, default=_now)

    conversation    = relationship("Conversation", back_populates="messages")
    recommandations = relationship("RecommandationIA", back_populates="message",
                                   cascade="all, delete-orphan")
    feedbacks       = relationship("FeedbackIA", back_populates="message",
                                   cascade="all, delete-orphan")


class RecommandationIA(Base):
    """Recommandation structurée extraite d'une réponse IA."""
    __tablename__ = "ia_recommandations"

    id              = Column(Integer, primary_key=True)
    org_id          = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("ia_conversations.id"), nullable=True)
    message_id      = Column(Integer, ForeignKey("ia_messages.id"), nullable=True)
    parcelle_id     = Column(Integer, ForeignKey("champ_parcelles.id"), nullable=True, index=True)
    culture_id      = Column(Integer, ForeignKey("agro_cultures.id"), nullable=True)
    categorie       = Column(Enum(CategorieReco), nullable=False)
    priorite        = Column(SmallInteger, default=3)   # 1=urgent, 5=info
    titre           = Column(String(200), nullable=False)
    action          = Column(Text, nullable=False)
    justification   = Column(Text)
    sources         = Column(JSONB)     # [{type:"regle",code:"MAL_001"}, ...]
    echeance_jours  = Column(Integer)
    statut          = Column(Enum(StatutReco), default=StatutReco.NOUVELLE, nullable=False)
    confiance       = Column(Float)
    created_at      = Column(DateTime, default=_now)

    conversation    = relationship("Conversation", back_populates="recommandations")
    message         = relationship("MessageIA", back_populates="recommandations")
    feedbacks       = relationship("FeedbackIA", back_populates="recommandation")


class FeedbackIA(Base):
    """Feedback utilisateur sur une réponse ou recommandation IA."""
    __tablename__ = "ia_feedback"

    id                = Column(Integer, primary_key=True)
    org_id            = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    conversation_id   = Column(Integer, ForeignKey("ia_conversations.id"), nullable=False)
    message_id        = Column(Integer, ForeignKey("ia_messages.id"), nullable=False)
    recommandation_id = Column(Integer, ForeignKey("ia_recommandations.id"), nullable=True)
    note              = Column(SmallInteger)    # 1-5 étoiles
    utile             = Column(Boolean)         # réponse utile ?
    commentaire       = Column(Text)
    amelioration      = Column(Text)
    created_at        = Column(DateTime, default=_now)

    conversation    = relationship("Conversation", back_populates="feedbacks")
    message         = relationship("MessageIA", back_populates="feedbacks")
    recommandation  = relationship("RecommandationIA", back_populates="feedbacks")


class ConfigIA(Base):
    """Configuration IA par organisation (1 ligne par org)."""
    __tablename__ = "ia_config"

    id                      = Column(Integer, primary_key=True)
    org_id                  = Column(Integer, ForeignKey("organizations.id"),
                                     unique=True, nullable=False)
    langue                  = Column(String(10), default="fr")
    ton                     = Column(Enum(TonAssistant), default=TonAssistant.SIMPLE)
    focus_cultures          = Column(ARRAY(String))
    inclure_meteo           = Column(Boolean, default=True)
    inclure_regles          = Column(Boolean, default=True)
    inclure_historique_sante = Column(Boolean, default=True)
    inclure_couts           = Column(Boolean, default=True)
    updated_at              = Column(DateTime, default=_now, onupdate=_now)
