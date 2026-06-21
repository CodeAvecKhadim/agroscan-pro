"""
Configuration centrale d'AgroScan Pro.
Toutes les valeurs sensibles proviennent de variables d'environnement (.env).
Aucune clé API n'est jamais écrite en dur dans le code.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Identité de l'application ---
    APP_NAME: str = "AgroScan Pro"
    COMPANY: str = "Social Technologie"
    CONTACT_PHONE: str = "+221 78 491 90 11"
    ENV: str = "development"

    # --- Base de données ---
    # SQLite pour démarrer (zéro config). En production : PostgreSQL.
    # ex : postgresql+psycopg://user:mdp@localhost:5432/agroscan
    DATABASE_URL: str = "sqlite:///./agroscan.db"

    # --- Sécurité / JWT ---
    SECRET_KEY: str = "CHANGER-EN-PRODUCTION-cle-tres-longue-et-aleatoire"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 h

    # --- Devise / fiscalité (Sénégal) ---
    CURRENCY: str = "FCFA"
    VAT_RATE: float = 0.18  # TVA 18 %

    # --- Quotas du plan gratuit ---
    FREE_MONTHLY_ANALYSES: int = 3
    FREE_HISTORY_DAYS: int = 30

    # --- Tarifs mensuels HT (en FCFA) — modifiables ---
    PRICE_PREMIUM_HT: int = 5000
    PRICE_COOP_HT: int = 25000

    # --- Connecteurs de paiement (à remplir : Wave / Orange Money / PayDunya) ---
    PAYMENT_PROVIDER: str = "manuel"   # manuel | wave | orange_money | paydunya
    PAYMENT_API_KEY: str = ""
    PAYMENT_WEBHOOK_SECRET: str = ""

    # --- Moteur de conseil (API Claude, optionnel) ---
    ANTHROPIC_API_KEY: str = ""

    # --- Reconnaissance de maladie par photo (Kindwise crop.health) ---
    CROP_HEALTH_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
