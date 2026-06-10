#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de seed — Base Agronomique AgroScan Pro.
Usage : python -m app.data.seed_agronomie [--reset]

  --reset : supprime et recrée les données (idempotent).
  Sans option : insère uniquement les cultures manquantes.
"""
import argparse
import logging
import sys

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models import Base
from app.models.agronomie import (
    Culture, Variete, ParametreClimatique, BesoinEau, BesoinNutritionnel,
    StadePhenologique, CalendrierCultural, RendementReference,
    Maladie, CultureMaladie, Ravageur, CultureRavageur, RecommandationCulture,
)
from app.data.grandes_cultures_seed import GRANDES_CULTURES_DATA
from app.data.maraichage_seed import MARAICHAGE_DATA
from app.data.arboriculture_seed import ARBORICULTURE_DATA

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

ALL_CULTURES = GRANDES_CULTURES_DATA + MARAICHAGE_DATA + ARBORICULTURE_DATA


def _get_or_create_maladie(db: Session, data: dict) -> Maladie:
    """Réutilise une maladie si elle existe déjà (partagée entre cultures)."""
    m = db.query(Maladie).filter_by(nom=data["nom"]).first()
    if not m:
        m = Maladie(
            nom=data["nom"],
            nom_scientifique=data.get("nom_scientifique"),
            pathogene_type=data.get("pathogene_type"),
            symptomes=data["symptomes"],
            conditions_favorables=data.get("conditions_favorables"),
        )
        db.add(m)
        db.flush()
    return m


def _get_or_create_ravageur(db: Session, data: dict) -> Ravageur:
    """Réutilise un ravageur si il existe déjà (partagé entre cultures)."""
    r = db.query(Ravageur).filter_by(nom=data["nom"]).first()
    if not r:
        r = Ravageur(
            nom=data["nom"],
            nom_scientifique=data.get("nom_scientifique"),
            type_ravageur=data.get("type_ravageur"),
            description=data.get("description"),
            symptomes_degats=data["symptomes_degats"],
        )
        db.add(r)
        db.flush()
    return r


def seed_culture(db: Session, cdata: dict) -> None:
    """Insère une culture et toutes ses sous-données."""
    nom = cdata["nom"]
    if db.query(Culture).filter_by(nom=nom).first():
        log.info(f"  SKIP  {nom} (déjà présente)")
        return

    log.info(f"  INSERT {nom}")
    culture = Culture(
        nom=nom,
        nom_scientifique=cdata.get("nom_scientifique"),
        nom_local=cdata.get("nom_local"),
        famille=cdata.get("famille"),
        categorie=cdata["categorie"],
        icone=cdata.get("icone", "🌱"),
        description=cdata.get("description"),
    )
    db.add(culture)
    db.flush()

    # Paramètres climatiques
    if pc := cdata.get("parametres_climatiques"):
        db.add(ParametreClimatique(culture_id=culture.id, **pc))

    # Variétés
    for v in cdata.get("varietes", []):
        db.add(Variete(culture_id=culture.id, **v))

    # Stades phénologiques
    for s in cdata.get("stades", []):
        db.add(StadePhenologique(culture_id=culture.id, **s))

    # Besoins en eau
    for e in cdata.get("besoins_eau", []):
        db.add(BesoinEau(culture_id=culture.id, **e))

    # Besoins nutritionnels
    for n in cdata.get("besoins_nutritionnels", []):
        db.add(BesoinNutritionnel(culture_id=culture.id, **n))

    # Calendriers culturaux
    for cal in cdata.get("calendriers", []):
        db.add(CalendrierCultural(culture_id=culture.id, **cal))

    # Rendements de référence
    for rend in cdata.get("rendements", []):
        db.add(RendementReference(culture_id=culture.id, **rend))

    # Maladies + liaison culture-maladie
    for mdata in cdata.get("maladies", []):
        join_fields = {
            k: mdata.pop(k, None)
            for k in ["frequence", "gravite", "stade_sensible",
                      "pertes_estimees", "prevention", "traitement"]
        }
        maladie = _get_or_create_maladie(db, mdata)
        db.add(CultureMaladie(
            culture_id=culture.id,
            maladie_id=maladie.id,
            **join_fields,
        ))

    # Ravageurs + liaison culture-ravageur
    for rdata in cdata.get("ravageurs", []):
        join_fields = {
            k: rdata.pop(k, None)
            for k in ["frequence", "gravite", "stade_sensible",
                      "pertes_estimees", "prevention", "lutte"]
        }
        ravageur = _get_or_create_ravageur(db, rdata)
        db.add(CultureRavageur(
            culture_id=culture.id,
            ravageur_id=ravageur.id,
            **join_fields,
        ))

    # Recommandations
    for rec in cdata.get("recommandations", []):
        db.add(RecommandationCulture(culture_id=culture.id, **rec))

    db.flush()


def reset_agro_tables(db: Session) -> None:
    """Supprime toutes les données agronomiques (ordre FK correct)."""
    log.warning("RESET — suppression des données agronomiques existantes")
    for model in [
        RecommandationCulture, CultureRavageur, CultureMaladie,
        Ravageur, Maladie, RendementReference, CalendrierCultural,
        BesoinNutritionnel, BesoinEau, StadePhenologique,
        ParametreClimatique, Variete, Culture,
    ]:
        db.query(model).delete()
    db.commit()
    log.info("Tables agronomiques vidées.")


def run(reset: bool = False) -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if reset:
            reset_agro_tables(db)

        log.info(f"Insertion de {len(ALL_CULTURES)} cultures…")
        for cdata in ALL_CULTURES:
            seed_culture(db, dict(cdata))  # copie pour éviter la mutation des pop()

        db.commit()
        total = db.query(Culture).count()
        log.info(f"✓ Seed terminé — {total} cultures en base.")
    except Exception as exc:
        db.rollback()
        log.error(f"Erreur seed : {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed base agronomique AgroScan Pro")
    parser.add_argument("--reset", action="store_true",
                        help="Supprime et recrée toutes les données agronomiques")
    args = parser.parse_args()
    run(reset=args.reset)
