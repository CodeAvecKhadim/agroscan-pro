"""
Schémas Pydantic v2 — Module IA Agricole AgroScan.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.ia import (
    CategorieReco, ModeConversation, RoleMessage,
    StatutConversation, StatutReco, TonAssistant,
)


# ── Config ────────────────────────────────────────────────────────────────────

class ConfigIAUpdate(BaseModel):
    langue:                   Optional[str]          = None
    ton:                      Optional[TonAssistant] = None
    focus_cultures:           Optional[list[str]]    = None
    inclure_meteo:            Optional[bool]         = None
    inclure_regles:           Optional[bool]         = None
    inclure_historique_sante: Optional[bool]         = None
    inclure_couts:            Optional[bool]         = None


class ConfigIAOut(BaseModel):
    id:                       int
    org_id:                   int
    langue:                   str
    ton:                      TonAssistant
    focus_cultures:           Optional[list[str]]  = None
    inclure_meteo:            bool
    inclure_regles:           bool
    inclure_historique_sante: bool
    inclure_couts:            bool

    model_config = {"from_attributes": True}


# ── Quota ─────────────────────────────────────────────────────────────────────

class QuotaIA(BaseModel):
    plan:               str
    conv_mois_utilisees: int
    conv_mois_limite:   Optional[int]   # None = illimité
    conv_restantes:     Optional[int]
    modele:             str


# ── Conversations ─────────────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    mode:        ModeConversation = ModeConversation.LIBRE
    parcelle_id: Optional[int]   = None
    culture_id:  Optional[int]   = None
    titre:       Optional[str]   = None
    message_initial: Optional[str] = Field(None, max_length=2000)


class ConversationOut(BaseModel):
    id:           int
    titre:        Optional[str]         = None
    mode:         ModeConversation
    statut:       StatutConversation
    nb_messages:  int
    tokens_total: int
    parcelle_id:  Optional[int]         = None
    culture_id:   Optional[int]         = None
    created_at:   datetime
    updated_at:   datetime

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id:             int
    titre:          Optional[str]        = None
    mode:           ModeConversation
    statut:         StatutConversation
    nb_messages:    int
    tokens_total:   int
    parcelle_id:    Optional[int]        = None
    parcelle_nom:   Optional[str]        = None
    culture_id:     Optional[int]        = None
    culture_nom:    Optional[str]        = None
    messages:       list["MessageOut"]   = []
    created_at:     datetime

    model_config = {"from_attributes": True}


# ── Messages ──────────────────────────────────────────────────────────────────

class MessageCreate(BaseModel):
    contenu: str = Field(..., min_length=1, max_length=2000)


class MessageOut(BaseModel):
    id:           int
    role:         RoleMessage
    contenu:      str
    tokens_in:    Optional[int]  = None
    tokens_out:   Optional[int]  = None
    modele:       Optional[str]  = None
    duree_ms:     Optional[int]  = None
    created_at:   datetime

    model_config = {"from_attributes": True}


class MessageAssistantOut(BaseModel):
    message:          MessageOut
    recommandations:  list["RecommandationOut"]  = []
    quota_restant:    Optional[int]              = None  # messages restants conv
    fallback_mode:    bool                       = False # True si réponse sans IA


# ── Recommandations ───────────────────────────────────────────────────────────

class RecommandationOut(BaseModel):
    id:              int
    categorie:       CategorieReco
    priorite:        int
    titre:           str
    action:          str
    justification:   Optional[str]      = None
    sources:         Optional[list]     = None
    echeance_jours:  Optional[int]      = None
    statut:          StatutReco
    confiance:       Optional[float]    = None
    parcelle_id:     Optional[int]      = None
    parcelle_nom:    Optional[str]      = None
    culture_id:      Optional[int]      = None
    culture_nom:     Optional[str]      = None
    created_at:      datetime

    model_config = {"from_attributes": True}


class RecoStatutUpdate(BaseModel):
    statut: StatutReco

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v == StatutReco.NOUVELLE:
            raise ValueError("Impossible de remettre en 'nouvelle'")
        return v


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    message_id:        int
    recommandation_id: Optional[int]  = None
    note:              Optional[int]  = Field(None, ge=1, le=5)
    utile:             Optional[bool] = None
    commentaire:       Optional[str]  = Field(None, max_length=1000)
    amelioration:      Optional[str]  = Field(None, max_length=500)

    @field_validator("note", "utile", mode="before")
    @classmethod
    def au_moins_un(cls, v):
        return v  # validation croisée dans model_validator

    def valide(self) -> bool:
        return self.note is not None or self.utile is not None


class FeedbackOut(BaseModel):
    id:                int
    message_id:        int
    recommandation_id: Optional[int]  = None
    note:              Optional[int]  = None
    utile:             Optional[bool] = None
    commentaire:       Optional[str]  = None
    amelioration:      Optional[str]  = None
    created_at:        datetime

    model_config = {"from_attributes": True}


# ── Contexte (debug/preview) ──────────────────────────────────────────────────

class ContexteAgro(BaseModel):
    producteur:   dict
    parcelles:    list[dict]
    sante:        dict
    ferme:        dict
    meteo:        dict
    regles:       dict
    date_contexte: str
    tokens_estimes: int


# ── Question rapide (sans conversation) ──────────────────────────────────────

class QuestionRapide(BaseModel):
    question:    str = Field(..., min_length=1, max_length=2000)
    parcelle_id: Optional[int] = None


class ReponseRapide(BaseModel):
    reponse:       str
    recommandations: list[RecommandationOut] = []
    modele:        Optional[str]             = None
    duree_ms:      int
    fallback_mode: bool                      = False


# ── Analyse parcelle ──────────────────────────────────────────────────────────

class AnalyseParcelle(BaseModel):
    conversation_id: int
    message_id:      int
    parcelle_nom:    str
    analyse:         str
    recommandations: list[RecommandationOut]
    score_sante:     Optional[int]   = None   # 0-100
    actions_urgentes: list[str]      = []
    duree_ms:        int


# Forward refs
ConversationDetail.model_rebuild()
MessageAssistantOut.model_rebuild()
