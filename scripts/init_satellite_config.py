"""
Script d'initialisation — Configuration Sentinel Hub (Phase 1).

Usage:
  python -m scripts.init_satellite_config --api-key YOUR_KEY --api-secret YOUR_SECRET
"""
import os
import sys
import argparse
from datetime import datetime, timezone

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, Base, engine
from app.models.satellite import SatelliteConfig


def init_satellite_config(api_key: str, api_secret: str):
    """Initialise les configurations Sentinel Hub."""
    print("Initializing Sentinel Hub configuration...")

    session = SessionLocal()

    try:
        # Vérifier si déjà configuré
        existing_key = session.query(SatelliteConfig).filter_by(
            key="sentinel_hub_api_key"
        ).first()

        if existing_key:
            print("⚠️  Configuration already exists. Updating...")
            existing_key.value = {"value": api_key}
            existing_key.updated_at = datetime.now(timezone.utc)
        else:
            print("✓ Creating configuration...")
            config_key = SatelliteConfig(
                key="sentinel_hub_api_key",
                value={"value": api_key},
                description="Sentinel Hub API Key (OAuth credentials)",
                is_secret=True,
            )
            session.add(config_key)

        # API Secret
        existing_secret = session.query(SatelliteConfig).filter_by(
            key="sentinel_hub_api_secret"
        ).first()

        if existing_secret:
            existing_secret.value = {"value": api_secret}
            existing_secret.updated_at = datetime.now(timezone.utc)
        else:
            config_secret = SatelliteConfig(
                key="sentinel_hub_api_secret",
                value={"value": api_secret},
                description="Sentinel Hub API Secret (OAuth credentials)",
                is_secret=True,
            )
            session.add(config_secret)

        # Configuration par défaut
        default_configs = [
            {
                "key": "sentinel_hub_api_url",
                "value": {"value": "https://services.sentinel-hub.com"},
                "description": "Base URL Sentinel Hub API",
                "is_secret": False,
            },
            {
                "key": "sentinel_hub_data_collection",
                "value": {"value": "sentinel-2-l2a"},
                "description": "Collection de données par défaut (sentinel-2-l2a ou sentinel-1-grd)",
                "is_secret": False,
            },
            {
                "key": "sentinel_hub_cloud_cover_max",
                "value": {"value": 50.0},
                "description": "Cloud cover max par défaut (%)",
                "is_secret": False,
            },
            {
                "key": "sentinel_hub_timeout_seconds",
                "value": {"value": 30},
                "description": "Timeout HTTP (secondes)",
                "is_secret": False,
            },
            {
                "key": "sentinel_hub_max_retries",
                "value": {"value": 3},
                "description": "Nombre max de retries",
                "is_secret": False,
            },
            {
                "key": "sentinel_hub_backoff_base_ms",
                "value": {"value": 1000},
                "description": "Backoff de base pour exponential backoff (ms)",
                "is_secret": False,
            },
        ]

        for cfg in default_configs:
            existing = session.query(SatelliteConfig).filter_by(key=cfg["key"]).first()
            if existing:
                print(f"  ✓ {cfg['key']} (already configured)")
            else:
                config = SatelliteConfig(
                    key=cfg["key"],
                    value=cfg["value"],
                    description=cfg["description"],
                    is_secret=cfg["is_secret"],
                )
                session.add(config)
                print(f"  ✓ {cfg['key']}")

        session.commit()
        print("\n✅ Sentinel Hub configuration initialized successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        return 1

    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Sentinel Hub configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.init_satellite_config --api-key YOUR_KEY --api-secret YOUR_SECRET
  
  Or set environment variables:
    export SENTINEL_HUB_API_KEY="your_key"
    export SENTINEL_HUB_API_SECRET="your_secret"
    python -m scripts.init_satellite_config
        """,
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="Sentinel Hub API Key",
        default=os.getenv("SENTINEL_HUB_API_KEY"),
    )
    parser.add_argument(
        "--api-secret",
        type=str,
        help="Sentinel Hub API Secret",
        default=os.getenv("SENTINEL_HUB_API_SECRET"),
    )

    args = parser.parse_args()

    if not args.api_key or not args.api_secret:
        print("❌ Error: API key and secret are required")
        print("\nProvide via CLI:")
        print("  --api-key YOUR_KEY --api-secret YOUR_SECRET")
        print("\nOr via environment variables:")
        print("  SENTINEL_HUB_API_KEY=xxx SENTINEL_HUB_API_SECRET=yyy")
        return 1

    return init_satellite_config(args.api_key, args.api_secret)


if __name__ == "__main__":
    sys.exit(main())
