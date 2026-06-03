"""
Système de crédits — AgroScan Pro.
Solde dans `wallets`, historique inviolable dans `credit_ledger`.
Débit atomique (verrou de ligne), "1 service payant à la fois", cooldown,
remboursement automatique si échec. Services gratuits (météo) exemptés.
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

COOLDOWN_MINUTES = 15


class CreditError(HTTPException):
    def __init__(self, detail: str, code: int = status.HTTP_402_PAYMENT_REQUIRED):
        super().__init__(status_code=code, detail=detail)


def _ensure_wallet(db: Session, user_id: int) -> None:
    db.execute(text("INSERT INTO wallets (user_id, solde) VALUES (:uid, 0) "
                    "ON CONFLICT (user_id) DO NOTHING"), {"uid": user_id})


def get_balance(db: Session, user_id: int) -> int:
    row = db.execute(text("SELECT solde FROM wallets WHERE user_id = :uid"),
                     {"uid": user_id}).first()
    return int(row[0]) if row else 0


def get_or_create_balance(db: Session, user_id: int) -> int:
    _ensure_wallet(db, user_id)
    db.commit()
    return get_balance(db, user_id)


def get_service(db: Session, code: str):
    return db.execute(text("SELECT id, code, nom, cout_credits, actif "
                           "FROM services WHERE code = :c"), {"c": code}).mappings().first()


def add_credits(db: Session, user_id: int, credits: int,
                motif: str = "achat", meta: Optional[dict] = None) -> int:
    _ensure_wallet(db, user_id)
    wal = db.execute(text("SELECT solde FROM wallets WHERE user_id = :uid FOR UPDATE"),
                     {"uid": user_id}).first()
    nouveau = int(wal[0]) + int(credits)
    db.execute(text("UPDATE wallets SET solde = :s, maj_le = now() WHERE user_id = :uid"),
               {"s": nouveau, "uid": user_id})
    db.execute(text("INSERT INTO credit_ledger (user_id, delta, motif, solde_apres, meta) "
                    "VALUES (:uid, :d, CAST(:m AS credit_motif), :sa, CAST(:meta AS jsonb))"),
               {"uid": user_id, "d": int(credits), "m": motif, "sa": nouveau,
                "meta": json.dumps(meta or {})})
    db.commit()
    return nouveau


def start_service(db: Session, user_id: int, service_code: str,
                  entree: Optional[dict] = None, farm_id: Optional[int] = None) -> int:
    svc = get_service(db, service_code)
    if not svc or not svc["actif"]:
        raise CreditError(f"Service inconnu ou inactif : {service_code}",
                          code=status.HTTP_404_NOT_FOUND)
    cout = int(svc["cout_credits"])

    _ensure_wallet(db, user_id)
    wal = db.execute(text("SELECT solde FROM wallets WHERE user_id = :uid FOR UPDATE"),
                     {"uid": user_id}).first()
    solde = int(wal[0]) if wal else 0

    actif = db.execute(text("SELECT 1 FROM service_requests WHERE user_id = :uid "
                            "AND statut IN ('en_attente','en_cours') LIMIT 1"),
                       {"uid": user_id}).first()
    if actif:
        db.rollback()
        raise CreditError("Un service est déjà en cours. Patientez qu'il se termine.",
                          code=status.HTTP_409_CONFLICT)

    last = db.execute(text("SELECT termine_le FROM service_requests WHERE user_id = :uid "
                           "AND statut = 'termine' AND termine_le IS NOT NULL "
                           "ORDER BY termine_le DESC LIMIT 1"), {"uid": user_id}).first()
    if last and last[0]:
        ecoule = datetime.now(timezone.utc) - last[0]
        if ecoule < timedelta(minutes=COOLDOWN_MINUTES):
            reste = max(1, COOLDOWN_MINUTES - int(ecoule.total_seconds() // 60))
            db.rollback()
            raise CreditError(f"Veuillez patienter encore ~{reste} min avant un nouveau service.",
                              code=status.HTTP_429_TOO_MANY_REQUESTS)

    if solde < cout:
        db.rollback()
        raise CreditError(f"Crédits insuffisants : {cout} requis, solde actuel {solde}.")

    rid = db.execute(text("INSERT INTO service_requests "
                          "(user_id, service_id, farm_id, statut, credits_debites, entree, demarre_le) "
                          "VALUES (:uid, :sid, :fid, 'en_cours', :cout, CAST(:e AS jsonb), now()) "
                          "RETURNING id"),
                     {"uid": user_id, "sid": svc["id"], "fid": farm_id, "cout": cout,
                      "e": json.dumps(entree or {})}).first()[0]

    if cout > 0:
        nouveau = solde - cout
        db.execute(text("UPDATE wallets SET solde = :s, maj_le = now() WHERE user_id = :uid"),
                   {"s": nouveau, "uid": user_id})
        db.execute(text("INSERT INTO credit_ledger (user_id, delta, motif, solde_apres, service_request_id) "
                        "VALUES (:uid, :d, 'service', :sa, :rid)"),
                   {"uid": user_id, "d": -cout, "sa": nouveau, "rid": rid})
    db.commit()
    return rid


def complete_service(db: Session, request_id: int, resultat: Optional[dict] = None) -> None:
    db.execute(text("UPDATE service_requests SET statut = 'termine', "
                    "resultat = CAST(:r AS jsonb), termine_le = now() "
                    "WHERE id = :rid AND statut = 'en_cours'"),
               {"rid": request_id, "r": json.dumps(resultat or {})})
    db.commit()


def fail_service(db: Session, request_id: int, erreur: str) -> None:
    req = db.execute(text("SELECT user_id, credits_debites FROM service_requests "
                          "WHERE id = :rid AND statut = 'en_cours' FOR UPDATE"),
                     {"rid": request_id}).first()
    if not req:
        db.rollback()
        return
    user_id, cout = int(req[0]), int(req[1] or 0)
    db.execute(text("UPDATE service_requests SET statut = 'echoue', erreur = :err, "
                    "termine_le = now() WHERE id = :rid"),
               {"rid": request_id, "err": (erreur or "")[:1000]})
    if cout > 0:
        wal = db.execute(text("SELECT solde FROM wallets WHERE user_id = :uid FOR UPDATE"),
                         {"uid": user_id}).first()
        nouveau = int(wal[0]) + cout
        db.execute(text("UPDATE wallets SET solde = :s, maj_le = now() WHERE user_id = :uid"),
                   {"s": nouveau, "uid": user_id})
        db.execute(text("INSERT INTO credit_ledger (user_id, delta, motif, solde_apres, service_request_id) "
                        "VALUES (:uid, :d, 'remboursement', :sa, :rid)"),
                   {"uid": user_id, "d": cout, "sa": nouveau, "rid": request_id})
    db.commit()


def recent_ledger(db: Session, user_id: int, limit: int = 10):
    rows = db.execute(text("SELECT delta, motif, solde_apres, cree_le FROM credit_ledger "
                           "WHERE user_id = :uid ORDER BY cree_le DESC LIMIT :lim"),
                      {"uid": user_id, "lim": limit}).mappings().all()
    return [dict(r) for r in rows]


TRIAL_CREDITS = 30  # credits d'essai offerts au particulier (3 services)


def account_type(db: Session, user_id: int) -> str:
    row = db.execute(text("SELECT account_type FROM users WHERE id = :uid"),
                     {"uid": user_id}).first()
    return row[0] if row else "particulier"


def grant_trial_if_needed(db: Session, user_id: int) -> int:
    """Offre les credits d'essai au particulier, une seule fois. Retourne le solde."""
    _ensure_wallet(db, user_id)
    db.execute(text("SELECT solde FROM wallets WHERE user_id = :uid FOR UPDATE"), {"uid": user_id})
    if account_type(db, user_id) != "particulier":
        db.commit()
        return get_balance(db, user_id)
    deja = db.execute(text("SELECT 1 FROM credit_ledger WHERE user_id = :uid "
                           "AND meta->>'raison' = 'essai_inscription' LIMIT 1"),
                      {"uid": user_id}).first()
    if deja:
        db.commit()
        return get_balance(db, user_id)
    solde = get_balance(db, user_id)
    nouveau = solde + TRIAL_CREDITS
    db.execute(text("UPDATE wallets SET solde = :s, maj_le = now() WHERE user_id = :uid"),
               {"s": nouveau, "uid": user_id})
    db.execute(text("INSERT INTO credit_ledger (user_id, delta, motif, solde_apres, meta) "
                    "VALUES (:uid, :d, 'bonus', :sa, CAST(:meta AS jsonb))"),
               {"uid": user_id, "d": TRIAL_CREDITS, "sa": nouveau,
                "meta": json.dumps({"raison": "essai_inscription"})})
    db.commit()
    return nouveau
