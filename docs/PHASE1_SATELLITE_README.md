"""
Phase 1 Satellite Sentinel Hub — README

Base de l'intégration Sentinel Hub.

## Architecture

### Modèles (app/models/satellite.py)
- `SatelliteProduct` : Métadonnées d'une image (product_id, date, cloud_cover, …)
- `SatelliteJob` : Orchestration des jobs (status, retry_logic, …)
- `SatelliteConfig` : Configuration Sentinel Hub (API keys, env, quotas)
- `SatelliteMetrics` : Indices calculés (NDVI, NDRE, NDMI, …) - *optionnel pour MVP*

### Services (app/services/satellite/)
- `SentinelHubClient` : Client HTTP pour Sentinel Hub API
  - `search_catalog()` : Recherche dans le catalogue (STAC)
  - `get_product_metadata()` : Récupère les métadonnées d'un produit
  - `submit_process_request()` : Soumet une requête Process API
  - `get_process_status()` : Polling du statut d'un job
  - `get_process_result()` : Récupère le résultat d'un job

- `get_evalscript_*()` : Générateurs de scripts d'évaluation
  - `get_evalscript_ndvi_ndre_ndmi()` : NDVI, NDRE, NDMI
  - `get_evalscript_savi_evi_msavi()` : SAVI, EVI, MSAVI

### Endpoints (app/routers/satellite.py)
Base: `/api/sante/precision/satellite`

- **POST /search** : Recherche produits dans le catalogue
  - Input: `SatelliteSearchRequest` (parcelle_id, sensor, dates, cloud_cover_max)
  - Output: `SatelliteSearchResponse` (produits trouvés, total_count)
  - Enregistre les produits dans `sc_satellite_products`

- **GET /products** : Liste les produits enregistrés
  - Query params: `parcelle_id`, `sensor` (optionnel)
  - Output: List[`SatelliteProductResponse`]

- **GET /jobs/{job_id}** : Statut d'un job
  - Output: `SatelliteJobResponse`

- **GET /jobs/parcelle/{parcelle_id}** : Liste des jobs d'une parcelle
  - Output: `BulkStatusResponse` (résumé des statuts)

- **POST /config** : Mettre à jour config Sentinel Hub (admin)
  - Input: `SatelliteConfigRequest` (key, value)
  - Output: `SatelliteConfigResponse`

- **GET /config/{key}** : Lire une config non-secret (admin)
  - Output: Dict (config)

- **GET /health** : Health check
  - Output: Dict (status: ok|error)

## Installation & Setup

### 1. Configuration Sentinel Hub

#### Option A : Via script Python
```bash
export SENTINEL_HUB_API_KEY="your-api-key-here"
export SENTINEL_HUB_API_SECRET="your-api-secret-here"

cd /opt/agroscan
python -m scripts.init_satellite_config
```

#### Option B : Via variable d'environnement
Ajouter au `.env` :
```
SENTINEL_HUB_API_KEY=your-key
SENTINEL_HUB_API_SECRET=your-secret
```

#### Option C : Via endpoint API
```bash
curl -X POST "http://localhost:8000/api/sante/precision/satellite/config" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "key": "sentinel_hub_api_key",
    "value": "your-api-key"
  }'
```

### 2. Dépendances
```bash
pip install httpx>=0.25.0
pip install sentinelhub>=3.11.5  # déjà installé
pip install pystac-client>=0.8.0  # optionnel pour STAC avancé
```

### 3. Créer les tables
```bash
cd /opt/agroscan
python
>>> from app.core.database import Base, engine
>>> Base.metadata.create_all(bind=engine)
>>> # ou via migrations Alembic si en production
```

### 4. Tests
```bash
cd /opt/agroscan
pytest tests/test_satellite_phase1.py -v
```

## Utilisation

### Exemple 1 : Rechercher des produits S2

```bash
curl -X POST "http://localhost:8000/api/sante/precision/satellite/search" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "parcelle_id": 1,
    "sensor": "sentinel-2",
    "date_from": "2026-05-01",
    "date_to": "2026-06-30",
    "cloud_cover_max": 30.0,
    "limit": 10
  }'
```

Réponse :
```json
{
  "parcelle_id": 1,
  "sensor": "sentinel-2",
  "products": [
    {
      "id": 42,
      "product_id": "S2A_MSIL2A_20260530T104031_N0510_R117_T31NDD_20260530T122534",
      "tile_id": "31NDD",
      "sensor": "sentinel-2",
      "date_acquisition": "2026-05-30",
      "cloud_cover": 12.5,
      "discovered_at": "2026-06-11T10:00:00Z"
    }
  ],
  "total_count": 5,
  "searched_at": "2026-06-11T10:05:00Z"
}
```

### Exemple 2 : Lister les produits

```bash
curl "http://localhost:8000/api/sante/precision/satellite/products?parcelle_id=1&sensor=sentinel-2" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Exemple 3 : Health check

```bash
curl "http://localhost:8000/api/sante/precision/satellite/health"
```

## Schémas de Données

### SatelliteProduct (sc_satellite_products)
```python
{
  "id": 42,                          # PK
  "parcelle_id": 1,                  # FK champ_parcelles
  "org_id": 1,                       # FK organizations (multi-tenancy)
  "product_id": "S2A_MSIL...",       # Unique Sentinel Hub ID
  "tile_id": "31NDD",                # UTM tile (S2 only)
  "sensor": "sentinel-2",            # sentinel-2 | sentinel-1
  "date_acquisition": "2026-05-30",  # Date de prise
  "date_product_date": "2026-05-30T...",  # Timestamp exact
  "cloud_cover": 12.5,               # %
  "snow_cover": 0.0,                 # %
  "footprint": {...},                # GeoJSON Polygon
  "product_url": "https://...",      # URL Sentinel Hub
  "is_cached": false,                # Données stockées localement ?
  "cached_at": null,
  "discovered_at": "2026-06-11T10:00:00Z",
  "created_at": "2026-06-11T10:00:00Z"
}
```

### SatelliteJob (sc_satellite_jobs)
```python
{
  "id": 123,                         # PK
  "parcelle_id": 1,                  # FK champ_parcelles
  "product_id": 42,                  # FK sc_satellite_products (nullable)
  "org_id": 1,                       # FK organizations
  "job_type": "search",              # search | process | fetch
  "status": "done",                  # queued | running | done | error
  "params": {...},                   # Paramètres input (JSONB)
  "result": {...},                   # Résultat (JSONB, si succès)
  "error_message": null,             # Message erreur (si erreur)
  "error_code": null,                # Code erreur Sentinel Hub
  "sentinelhub_job_id": "abc123",    # Job ID pour polling
  "started_at": "2026-06-11T10:10:00Z",
  "completed_at": "2026-06-11T10:15:30Z",
  "created_at": "2026-06-11T10:05:00Z",
  "retry_count": 0,
  "max_retries": 3,
  "next_retry_at": null
}
```

### SatelliteConfig (sc_satellite_config)
```python
{
  "id": 1,                           # PK
  "key": "sentinel_hub_api_key",     # Unique identifier
  "value": {"value": "secret..."},   # JSONB (peut être JSON, nombre, texte)
  "description": "Sentinel Hub API Key",
  "is_secret": true,                 # Ne pas logguer si true
  "updated_at": "2026-06-11T10:00:00Z",
  "created_at": "2026-06-11T10:00:00Z"
}
```

## Notes de Conception

### Multi-tenant
- Tous les enregistrements incluent `org_id` pour l'isolation
- Les endpoints vérifient l'accès (`user.org_id == parcelle.org_id`)

### Authentification Sentinel Hub
- Basic Auth (API Key:API Secret en base64)
- Stocké en DB (SatelliteConfig) avec flag `is_secret`
- À faire: Rotation de clés, expiration

### Gestion des erreurs
- Retry logic implémenté dans le modèle (retry_count, max_retries, next_retry_at)
- Backoff exponentiel à implémenter en Phase 2
- Logging via `logging` (voir app/services/satellite/client.py)

### Performance
- Index sur `(parcelle_id, date_acquisition)` pour requêtes récentes
- Index sur `(parcelle_id, status)` pour les jobs en cours
- Cache TTL en SatelliteProduct via `expire_le` (utiliser en Phase 3+)

## Phase 2 (à venir)

- Implémentation du Process API
- Calcul effectif des indices (NDVI, NDRE, NDMI, …)
- Stockage dans SatelliteMetrics (ou réutilisation de sc_indices_satellitaires)
- Retry logic avec backoff exponentiel

## Troubleshooting

### "Sentinel Hub configuration not found"
**Symptôme**: Erreur 500 lors de POST /search
**Solution**: Exécuter `scripts/init_satellite_config.py` pour créer la config

### "Network error" / "Connection timeout"
**Symptôme**: Sentinel Hub API call fails
**Solution**: 
- Vérifier la connectivité réseau
- Vérifier les clés API
- Vérifier l'endpoint Sentinel Hub

### "Product already exists, skipping"
**Symptôme**: Produit pas nouveau après recherche
**Solution**: Normal - les produits sont dédupliqués par product_id

## Références

- Sentinel Hub API: https://documentation.sentinel-hub.com/
- STAC Spec: https://stacspec.org/
- Process API: https://documentation.sentinel-hub.com/api/reference/api/processing/
"""

# EOF
