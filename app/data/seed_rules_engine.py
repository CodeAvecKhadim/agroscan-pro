"""
Seed script — Rules Engine V1 (toutes catégories).
Usage : .venv/bin/python -m app.data.seed_rules_engine [--reset]
"""
import sys
import logging
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.rules_engine import RegleMoteur, RegleCulture, RegleEntite
from app.models.agronomie import Culture, Maladie, Ravageur
from app.models import rules_engine as re_models
from app.core.database import Base
from app.data.rules.maladies_rules import MALADIES_RULES
from app.data.rules.ravageurs_rules import RAVAGEURS_RULES
from app.data.rules.fertilisation_rules import FERTILISATION_RULES
from app.data.rules.irrigation_rules import IRRIGATION_RULES
from app.data.rules.meteo_rules import METEO_RULES
from app.data.rules.calendrier_rules import CALENDRIER_RULES
from app.data.rules.rendement_rules import RENDEMENT_RULES

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def _ensure_tables():
    Base.metadata.create_all(bind=engine)
    log.info("Tables re_* vérifiées/créées.")


def _reset(db: Session):
    db.query(RegleEntite).delete()
    db.query(RegleCulture).delete()
    db.query(RegleMoteur).delete()
    db.commit()
    log.info("Tables rules engine vidées.")


def _get_culture_id(db: Session, nom: str) -> int | None:
    c = db.query(Culture).filter_by(nom=nom).first()
    if not c:
        log.warning("Culture introuvable : %s", nom)
    return c.id if c else None


def _get_maladie_id(db: Session, nom: str) -> int | None:
    m = db.query(Maladie).filter_by(nom=nom).first()
    if not m:
        log.warning("Maladie introuvable : %s", nom)
    return m.id if m else None


def _get_ravageur_id(db: Session, nom: str) -> int | None:
    r = db.query(Ravageur).filter_by(nom=nom).first()
    if not r:
        log.warning("Ravageur introuvable : %s", nom)
    return r.id if r else None


def seed(db: Session, rules: list[dict]):
    created = 0
    skipped = 0

    for r in rules:
        if db.query(RegleMoteur).filter_by(code=r["code"]).first():
            skipped += 1
            continue

        regle = RegleMoteur(
            code=r["code"],
            categorie=r["categorie"],
            sous_categorie=r.get("sous_categorie"),
            nom=r["nom"],
            zones_applicables=r.get("zones_applicables"),
            stades_applicables=r.get("stades_applicables"),
            mois_applicables=r.get("mois_applicables"),
            conditions=r["conditions"],
            actions=r["actions"],
            gravite=r["gravite"],
            priorite=r.get("priorite", 5),
            confiance=r.get("confiance", 0.80),
            plan_requis=r.get("plan_requis", "gratuit"),
            active=True,
            version="1.0",
        )
        db.add(regle)
        db.flush()

        # Cultures liées
        for culture_nom in r.get("cultures", []):
            cid = _get_culture_id(db, culture_nom)
            if cid:
                db.add(RegleCulture(regle_id=regle.id, culture_id=cid))

        # Entités maladies
        for maladie_nom in r.get("maladies", []):
            mid = _get_maladie_id(db, maladie_nom)
            if mid:
                db.add(RegleEntite(regle_id=regle.id, entite_type="maladie", entite_id=mid))

        # Entités ravageurs
        for ravageur_nom in r.get("ravageurs", []):
            rid = _get_ravageur_id(db, ravageur_nom)
            if rid:
                db.add(RegleEntite(regle_id=regle.id, entite_type="ravageur", entite_id=rid))

        created += 1

    db.commit()
    return created, skipped


def main():
    reset = "--reset" in sys.argv
    _ensure_tables()

    db = SessionLocal()
    try:
        if reset:
            _reset(db)

        all_categories = [
            ("maladies",      MALADIES_RULES),
            ("ravageurs",     RAVAGEURS_RULES),
            ("fertilisation", FERTILISATION_RULES),
            ("irrigation",    IRRIGATION_RULES),
            ("meteo",         METEO_RULES),
            ("calendrier",    CALENDRIER_RULES),
            ("rendement",     RENDEMENT_RULES),
        ]

        total_created = 0
        total_skipped = 0
        for cat_name, cat_rules in all_categories:
            created, skipped = seed(db, cat_rules)
            log.info("  %-14s : %d créées, %d ignorées", cat_name, created, skipped)
            total_created += created
            total_skipped += skipped

        log.info("Seed terminé : %d créées, %d ignorées", total_created, total_skipped)

        total = db.query(RegleMoteur).count()
        log.info("Total règles en base : %d", total)

        # Rapport par catégorie
        log.info("\n── Rapport par catégorie ──")
        cats = ["maladie", "ravageur", "fertilisation", "irrigation", "meteo", "calendrier", "rendement"]
        for cat in cats:
            n = db.query(RegleMoteur).filter(RegleMoteur.categorie == cat).count()
            log.info("  %-16s : %d règles", cat, n)

    finally:
        db.close()


if __name__ == "__main__":
    main()
