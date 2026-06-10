"""
Point d'entrée de l'API AgroScan Pro.
Assemble les routeurs, configure CORS, crée les tables au démarrage et sert l'interface.
Lancer en développement :  uvicorn app.main:app --reload
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os

from app.core.config import settings
from app.core.database import Base, engine
from app.core.limiter import limiter
from app.routers import auth, analyses, billing, coop, fertilite, credits, parcelles, agronomie, rules_engine, champ, sante, ferme, meteo, ia
from app.services.crop_health import identifier_maladie, CropHealthError

# Création automatique des tables (en production : utiliser Alembic pour les migrations).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Plateforme SaaS d'analyse de sol — Social Technologie (Sénégal)",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# CORS : origines explicites. Configurer ALLOWED_ORIGINS dans .env pour la production.
_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
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
app.include_router(credits.router)
app.include_router(parcelles.router)
app.include_router(agronomie.router)
app.include_router(rules_engine.router)
app.include_router(champ.router)
app.include_router(sante.router)
app.include_router(ferme.router)
app.include_router(meteo.router)
app.include_router(ia.router)


@app.get("/api/health", tags=["Système"])
def health():
    """Vérifie que l'API répond."""
    return {"status": "ok", "app": settings.APP_NAME, "company": settings.COMPANY}


# --- Interface web (sert le fichier statique) ---
STATIC_DIR  = os.path.join(os.path.dirname(__file__), "static")
UPLOADS_DIR = "/opt/agroscan/uploads"
app.mount("/static",  StaticFiles(directory=STATIC_DIR),  name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


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

@app.get("/calendrier", include_in_schema=False)
def page_calendrier():
    """Calendrier cultural : étapes clés d'une culture selon la date de semis."""
    return _page("calendrier.html")


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
