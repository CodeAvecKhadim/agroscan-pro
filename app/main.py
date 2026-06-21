"""
Point d'entrée de l'API AgroScan Pro.
Assemble les routeurs, configure CORS, crée les tables au démarrage et sert l'interface.
Lancer en développement :  uvicorn app.main:app --reload
"""
import logging
import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import (
    account, admin, agronomie, analyses,
    app_activites, app_exploitation, app_export_excel, app_export_pdf, app_photo, app_satellite,
    auth, beta_admin, billing,
    champ, conseiller, coop, credits,
    ferme, fertilite,
    ia,
    meteo,
    observations_terrain, otp,
    rapports_pdf, rules_engine,
    sante, sante_cultures, satellite,
)
from app.services.crop_health import identifier_maladie, CropHealthError

log = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Plateforme SaaS d'analyse de sol — Social Technologie (Sénégal)",
    version="1.0.0",
)

ALLOWED_ORIGINS = [
    "https://agroscanpro.com",
    "https://www.agroscanpro.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(account.router)
app.include_router(otp.router)
app.include_router(analyses.router)
app.include_router(billing.router)
app.include_router(credits.router)
app.include_router(coop.router)
app.include_router(fertilite.router)
app.include_router(agronomie.router)
app.include_router(champ.router)
app.include_router(ferme.router)
app.include_router(meteo.router)
app.include_router(ia.router)
app.include_router(sante.router)
app.include_router(sante_cultures.router)
app.include_router(satellite.router)
app.include_router(conseiller.router)
app.include_router(observations_terrain.router)
app.include_router(app_activites.router)
app.include_router(app_exploitation.router)
app.include_router(app_photo.router)
app.include_router(app_satellite.router)
app.include_router(app_export_excel.router)
app.include_router(app_export_pdf.router)
app.include_router(rapports_pdf.router)
app.include_router(rules_engine.router)
app.include_router(admin.router)
app.include_router(beta_admin.router)


@app.on_event("startup")
async def startup_checks():
    """Avertit au démarrage si des clés API optionnelles sont manquantes."""
    optional_keys = {
        "ANTHROPIC_API_KEY": "IA Polélé (conseils intelligents)",
        "CROP_HEALTH_API_KEY": "Diagnostic photo Kindwise",
        "PAYMENT_API_KEY": "Paiement PayDunya",
    }
    for key, feature in optional_keys.items():
        if not getattr(settings, key, ""):
            log.warning("Clé manquante : %s — fonctionnalité désactivée : %s", key, feature)


@app.get("/api/health", tags=["Système"])
def health():
    """Vérifie que l'API répond."""
    return {"status": "ok", "app": settings.APP_NAME, "company": settings.COMPANY}


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _page(nom: str) -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, nom))


@app.get("/", include_in_schema=False)
def index(): return _page("index.html")

@app.get("/carte", include_in_schema=False)
def page_carte(): return _page("carte.html")

@app.get("/saisie", include_in_schema=False)
def page_saisie(): return _page("saisie.html")

@app.get("/oad", include_in_schema=False)
def page_oad(): return _page("oad.html")

@app.get("/scan", include_in_schema=False)
def page_scan(): return _page("scan.html")

@app.get("/resultat", include_in_schema=False)
def page_resultat(): return _page("resultat.html")

@app.get("/cultures", include_in_schema=False)
def page_cultures(): return _page("cultures.html")

@app.get("/vitrine", include_in_schema=False)
def page_vitrine(): return _page("vitrine.html")

@app.get("/tarifs", include_in_schema=False)
def page_tarifs(): return _page("tarifs.html")

@app.get("/activites", include_in_schema=False)
def page_activites(): return _page("activites.html")

@app.get("/admin", include_in_schema=False)
def page_admin(): return _page("admin.html")

@app.get("/app", include_in_schema=False)
def page_app(): return _page("app.html")

@app.get("/calendrier", include_in_schema=False)
def page_calendrier(): return _page("calendrier.html")

@app.get("/conseiller", include_in_schema=False)
def page_conseiller(): return _page("conseiller.html")

@app.get("/coop", include_in_schema=False)
def page_coop(): return _page("coop.html")

@app.get("/exploitation", include_in_schema=False)
def page_exploitation(): return _page("exploitation.html")

@app.get("/ferme", include_in_schema=False)
def page_ferme(): return _page("ferme.html")

@app.get("/ia", include_in_schema=False)
def page_ia(): return _page("ia.html")

@app.get("/meteo", include_in_schema=False)
def page_meteo(): return _page("meteo.html")

@app.get("/mon-champ", include_in_schema=False)
def page_mon_champ(): return _page("mon-champ.html")

@app.get("/offline", include_in_schema=False)
def page_offline(): return _page("offline.html")

@app.get("/photo", include_in_schema=False)
def page_photo(): return _page("photo.html")

@app.get("/sante", include_in_schema=False)
def page_sante(): return _page("sante.html")

@app.get("/sante-cultures", include_in_schema=False)
def page_sante_cultures(): return _page("sante-cultures.html")


@app.post("/api/scan-maladie", tags=["Diagnostic"])
async def scan_maladie(photo: UploadFile = File(...)):
    """Reçoit une photo de feuille et renvoie un diagnostic Kindwise côté serveur."""
    if not settings.CROP_HEALTH_API_KEY:
        raise HTTPException(status_code=503, detail="Service de diagnostic photo non configuré.")
    contenu = await photo.read()
    if not contenu:
        raise HTTPException(status_code=400, detail="Photo vide.")
    if len(contenu) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Photo trop lourde (max 8 Mo).")
    try:
        return identifier_maladie(contenu, langue="fr")
    except CropHealthError as e:
        raise HTTPException(status_code=502, detail=str(e))
