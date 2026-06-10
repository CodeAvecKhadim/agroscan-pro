"""
Bilans agronomiques et financiers — Module GESTION DE FERME.
Agrège activités, coûts, main-d'œuvre, rendements par parcelle/campagne.
"""
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ferme import Activite, Cout, MainOeuvre, TypeActivite, CategorieCoût, StatutActivite
from app.models.champ import Parcelle
from app.models.agronomie import Culture, RendementReference
from app.schemas.ferme import BilanParcelle, LigneActiviteBilan
from app.services.ferme.activite import ecart_rendement


def bilan_parcelle(
    db: Session,
    parcelle_id: int,
    org_id: int,
    periode_debut: Optional[date] = None,
    periode_fin: Optional[date] = None,
) -> BilanParcelle:
    """Bilan complet d'une parcelle sur une période."""
    parcelle = db.query(Parcelle).filter_by(id=parcelle_id).first()
    culture_nom = None
    surface_ha  = parcelle.superficie_ha if parcelle else None

    if parcelle and parcelle.culture_id:
        c = db.query(Culture).filter_by(id=parcelle.culture_id).first()
        culture_nom = c.nom if c else None

    # Requête activités
    q = db.query(Activite).filter_by(org_id=org_id, parcelle_id=parcelle_id)
    if periode_debut:
        q = q.filter(Activite.date_prevue >= periode_debut)
    if periode_fin:
        q = q.filter(Activite.date_prevue <= periode_fin)
    activites = q.order_by(Activite.date_prevue).all()

    # Coûts + MO par catégorie
    intrants = materiel = transport = mo_total = autre = 0
    for a in activites:
        for c in a.couts:
            m = c.montant_total_fcfa or 0
            if c.categorie == CategorieCoût.INTRANT:    intrants  += m
            elif c.categorie == CategorieCoût.MATERIEL: materiel  += m
            elif c.categorie == CategorieCoût.TRANSPORT:transport += m
            else:                                        autre     += m
        for m_obj in a.main_oeuvre:
            mo_total += m_obj.montant_total_fcfa or 0

    cout_total = intrants + materiel + transport + mo_total + autre
    cout_par_ha = int(cout_total / surface_ha) if surface_ha and surface_ha > 0 else None

    # Rendement depuis activité récolte
    rendement_reel = None
    for a in activites:
        if a.type == TypeActivite.RECOLTE and a.statut == StatutActivite.TERMINE:
            rend = (a.details or {}).get("rendement_kg_ha")
            if rend:
                rendement_reel = float(rend)
                break

    # Rendement de référence
    rendement_ref = None
    if parcelle and parcelle.culture_id:
        ref = (db.query(RendementReference)
               .filter_by(culture_id=parcelle.culture_id,
                          zone_agro=parcelle.zone_agro)
               .first())
        if ref and ref.rendement_moyen_t_ha:
            rendement_ref = float(ref.rendement_moyen_t_ha) * 1000  # t/ha → kg/ha

    # Lignes activités
    lignes = []
    for a in activites:
        nb_p = len(a.preuves)
        ct   = sum(c.montant_total_fcfa or 0 for c in a.couts) + sum(m.montant_total_fcfa or 0 for m in a.main_oeuvre)
        lignes.append(LigneActiviteBilan(
            id=a.id, type=a.type, titre=a.titre,
            statut=a.statut, date_prevue=a.date_prevue,
            date_fin=a.date_fin, cout_total_fcfa=ct, nb_preuves=nb_p,
        ))

    return BilanParcelle(
        parcelle_id              = parcelle_id,
        parcelle_nom             = parcelle.nom if parcelle else None,
        culture_nom              = culture_nom,
        surface_ha               = surface_ha,
        periode_debut            = periode_debut,
        periode_fin              = periode_fin,
        nb_activites             = len(activites),
        activites                = lignes,
        cout_intrants_fcfa       = intrants,
        cout_materiel_fcfa       = materiel,
        cout_transport_fcfa      = transport,
        cout_main_oeuvre_fcfa    = mo_total,
        cout_autre_fcfa          = autre,
        cout_total_fcfa          = cout_total,
        cout_par_ha_fcfa         = cout_par_ha,
        rendement_kg_ha          = rendement_reel,
        rendement_reference_kg_ha = rendement_ref,
        ecart_rendement_pct      = ecart_rendement(rendement_reel, rendement_ref) if rendement_reel else None,
        genere_le                = datetime.now(timezone.utc),
    )
