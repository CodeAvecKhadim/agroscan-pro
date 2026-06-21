"""
Point d'entrée de l'API AgroScan Pro.
Assemble les routeurs, configure CORS, crée les tables au démarrage et sert l'interface.
Lancer en développement :  uvicorn app.main:app --reload
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth, analyses, billing, coop, fertilite
from app.services.crop_health import identifier_maladie, CropHealthError

# Création automatique des tables (en production : utiliser Alembic pour les migrations).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Plateforme SaaS d'analyse de sol — Social Technologie (Sénégal)",
    version="1.0.0",
)

# CORS : autoriser le front (à restreindre à votre domaine en production).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routeurs
app.include_router(auth.router)
app.include_router(analyses.router)
app.include_router(billing.router)
app.include_router(coop.router)
app.include_router(fertilite.router)


@app.get("/api/health", tags=["Système"])
def health():
    """Vérifie que l'API répond."""
    return {"status": "ok", "app": settings.APP_NAME, "company": settings.COMPANY}


# --- Interface web (sert le fichier statique) ---
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# --- Pages des modules de l'Outil d'Aide à la Décision (OAD) ---
def _page(nom):
    return FileResponse(os.path.join(STATIC_DIR, nom))

@app.get("/carte", include_in_schema=False)
def page_carte():
    """Étape 1 : cartographie de la parcelle (Leaflet + surface)."""
    return _page("carte.html")

@app.get("/saisie", include_in_schema=False)
def page_saisie():
    """Étape 2 : saisie des mesures du capteur + météo."""
    return _page("saisie.html")

@app.get("/oad", include_in_schema=False)
def page_oad():
    """Analyse de sol par capteur (29 cultures) avec lecture vocale."""
    return _page("oad.html")

@app.get("/scan", include_in_schema=False)
def page_scan():
    """Diagnostic d'une maladie par photo."""
    return _page("scan.html")

@app.get("/resultat", include_in_schema=False)
def page_resultat():
    """Étape 3 : rapport agronomique final (score, conseils, audio)."""
    return _page("resultat.html")

@app.get("/cultures", include_in_schema=False)
def page_cultures():
    """Galerie des 29 cultures avec photos."""
    return _page("cultures.html")

@app.get("/vitrine", include_in_schema=False)
def page_vitrine():
    """Pages publiques : accueil, fonctionnalités, tarifs, à propos, contact."""
    return _page("vitrine.html")

@app.get("/tarifs", include_in_schema=False)
def page_tarifs():
    """Page Tarifs : 4 offres avec sélecteur de durée et réductions."""
    return _page("tarifs.html")




# --- Pages modules avancés (ajoutées automatiquement) ---
@app.get("/activites", include_in_schema=False)
def page_activites():
    """Suivi des activités agricoles sur la parcelle."""
    return _page("activites.html")

@app.get("/admin", include_in_schema=False)
def page_admin():
    """Interface d'administration (accès restreint en production)."""
    return _page("admin.html")

@app.get("/app", include_in_schema=False)
def page_app():
    """Application principale."""
    return _page("app.html")

@app.get("/calendrier", include_in_schema=False)
def page_calendrier():
    """Calendrier cultural : dates semis, récolte, activités."""
    return _page("calendrier.html")

@app.get("/conseiller", include_in_schema=False)
def page_conseiller():
    """Interface conseiller agricole (vue technique complète)."""
    return _page("conseiller.html")

@app.get("/coop", include_in_schema=False)
def page_coop():
    """Espace coopérative."""
    return _page("coop.html")

@app.get("/exploitation", include_in_schema=False)
def page_exploitation():
    """Mon exploitation : surface, production, coûts, revenus."""
    return _page("exploitation.html")

@app.get("/ferme", include_in_schema=False)
def page_ferme():
    """Gestion de la ferme et des parcelles."""
    return _page("ferme.html")

@app.get("/ia", include_in_schema=False)
def page_ia():
    """Assistant IA Polélé — conseils agronomiques intelligents."""
    return _page("ia.html")

@app.get("/meteo", include_in_schema=False)
def page_meteo():
    """Météo temps réel et alertes agronomiques (Open-Meteo)."""
    return _page("meteo.html")

@app.get("/mon-champ", include_in_schema=False)
def page_mon_champ():
    """Vue détaillée du champ sélectionné."""
    return _page("mon-champ.html")

@app.get("/offline", include_in_schema=False)
def page_offline():
    """Page hors ligne (PWA fallback)."""
    return _page("offline.html")

@app.get("/photo", include_in_schema=False)
def page_photo():
    """Diagnostic photo de cultures / maladies."""
    return _page("photo.html")

@app.get("/sante", include_in_schema=False)
def page_sante():
    """Santé des cultures : maladies, ravageurs, traitements."""
    return _page("sante.html")

@app.get("/sante-cultures", include_in_schema=False)
def page_sante_cultures():
    """Tableau de bord santé cultures avec indices satellite."""
    return _page("sante-cultures.html")


@app.post("/api/scan-maladie", tags=["Diagnostic"])
async def scan_maladie(photo: UploadFile = File(...)):
    """
    Reçoit une photo de feuille et renvoie un diagnostic de maladie via crop.health.
    La clé API reste côté serveur. Renvoie {disponible, maladies:[...]}.
    """
    if not settings.CROP_HEALTH_API_KEY:
        raise HTTPException(status_code=503,
            detail="Service de diagnostic photo non configuré.")
    contenu = await photo.read()
    if not contenu:
        raise HTTPException(status_code=400, detail="Photo vide.")
    if len(contenu) > 8 * 1024 * 1024:   # garde-fou : 8 Mo max
        raise HTTPException(status_code=413, detail="Photo trop lourde (max 8 Mo).")
    try:
        return identifier_maladie(contenu, langue="fr")
    except CropHealthError as e:
        raise HTTPException(status_code=502, detail=str(e))
