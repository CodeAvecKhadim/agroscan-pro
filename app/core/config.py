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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 h

    # --- Devise / fiscalité (Sénégal) ---
    CURRENCY: str = "FCFA"
    VAT_RATE: float = 0.18  # TVA 18 %

    # --- Quotas plan gratuit ---
    FREE_DAILY_AI_ANALYSES: int = 3          # analyses IA par jour
    FREE_WEEKLY_SATELLITE: int = 1           # analyse satellite par semaine
    FREE_MAX_PARCELLES: int = 2              # parcelles max
    FREE_MAX_HA_PER_PARCELLE: float = 3.0   # hectares max par parcelle
    # legacy compat
    FREE_MONTHLY_ANALYSES: int = 3
    FREE_HISTORY_DAYS: int = 30

    # --- Tarifs HT (en FCFA) ---
    # Producteur Premium : prix par campagne agricole (90 jours)
    PRICE_PREMIUM_HT: int = 14900
    PRICE_PREMIUM_DURATION_DAYS: int = 90   # durée campagne = 3 mois
    # Coopérative : mensuel ou annuel
    PRICE_COOP_HT: int = 25000              # mensuel
    PRICE_COOP_HT_ANNUAL: int = 250000      # annuel (250 000 FCFA / an)
    COOP_INCLUDED_HA: int = 25              # hectares inclus dans le plan de base

    # --- CORS (séparer par virgule dans .env : https://mondomaine.com,https://api.mondomaine.com) ---
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://localhost:3000"

    # --- Connecteurs de paiement ---
    PAYMENT_PROVIDER: str = "manuel"   # manuel | wave | orange_money | paydunya
    PAYMENT_API_KEY: str = ""
    PAYMENT_WEBHOOK_SECRET: str = ""
    # URL de retour post-paiement (surcharger en production)
    PAYMENT_SUCCESS_URL: str = "http://localhost:8000/app?payment=success"
    PAYMENT_ERROR_URL: str = "http://localhost:8000/app?payment=error"
    # Wave Money (Sénégal)
    WAVE_API_KEY: str = ""             # Bearer token Wave Merchant API
    WAVE_CHECKOUT_URL: str = "https://api.wave.com/v1/checkout/sessions"
    # Orange Money (Sénégal)
    ORANGE_API_KEY: str = ""           # clé Orange Money Merchant API
    ORANGE_AUTH_HEADER: str = ""       # Authorization header Orange API
    ORANGE_CHECKOUT_URL: str = "https://api.orange.com/orange-money-webpay/dev/v1/webpayment"
    # PayDunya
    PAYDUNYA_MASTER_KEY: str = ""
    PAYDUNYA_PRIVATE_KEY: str = ""
    PAYDUNYA_TOKEN: str = ""
    PAYDUNYA_PUBLIC_KEY: str = ""
    PAYDUNYA_MODE: str = "test"        # test | live
    PAYDUNYA_STORE_NAME: str = "AgroScan Pro"
    PAYDUNYA_CHECKOUT_URL: str = ""    # auto-résolu depuis PAYDUNYA_MODE

    # --- Moteur de conseil (API Claude, optionnel) ---
    ANTHROPIC_API_KEY: str = ""

    # --- Reconnaissance de maladie par photo (Kindwise crop.health) ---
    CROP_HEALTH_API_KEY: str = ""

    # --- Sentinel Hub (Copernicus) — analyse satellite Sentinel-2 ---
    SENTINELHUB_CLIENT_ID: str = ""
    SENTINELHUB_CLIENT_SECRET: str = ""

    # --- Notifications (webhook + SMS) ---
    NOTIFICATION_WEBHOOK_URL: str = ""
    NOTIFICATION_SECRET: str = ""
    SMS_PROVIDER: str = "mock"       # mock | auto | orange | free | expresso | africas_talking
    SMS_API_KEY: str = ""
    SMS_API_SECRET: str = ""         # utilisé par certains opérateurs (ex. Free Sénégal)
    SMS_USERNAME: str = "sandbox"
    SMS_SENDER_ID: str = "AgroScan"
    # URLs passerelle SMS (opérateurs directs)
    ORANGE_SMS_URL: str = "https://api.orange.com/smsmessaging/v1"
    FREE_SMS_URL: str = "https://sms.free.sn/api/v1"
    EXPRESSO_SMS_URL: str = "https://sms.expresso.sn/api"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
