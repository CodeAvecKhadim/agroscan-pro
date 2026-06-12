"""
Service Satellite — Client Sentinel Hub.

Authentification et requêtes vers Sentinel Hub API.
"""
import logging
import os
from typing import Optional, Dict, List, Any, Tuple
from datetime import date, datetime, timedelta
from dataclasses import dataclass

import httpx
from sentinelhub import SentinelHubRequest, SentinelHubCatalog, CRS, BBox, bbox_to_dimensions

log = logging.getLogger(__name__)


@dataclass
class SentinelHubConfig:
    """Configuration Sentinel Hub."""
    api_key: str
    api_secret: str
    api_url: str = "https://services.sentinel-hub.com"
    data_collection: str = "sentinel-2-l2a"  # Default: Sentinel-2 Level 2A
    max_cloud_cover: float = 50.0


class SentinelHubClient:
    """Client pour interagir avec Sentinel Hub API."""

    def __init__(self, config: SentinelHubConfig):
        self.config = config
        self.api_url = config.api_url
        self.api_key = config.api_key
        self.api_secret = config.api_secret
        self.data_collection = config.data_collection
        self.max_cloud_cover = config.max_cloud_cover
        
        # Client HTTP
        self.client = httpx.Client(timeout=30.0)
        
        log.info(f"SentinelHubClient initialized with data_collection={self.data_collection}")

    def search_catalog(
        self,
        bbox: Dict[str, float],  # {min_lon, min_lat, max_lon, max_lat}
        date_from: date,
        date_to: date,
        sensor: str = "sentinel-2",
        cloud_cover_max: Optional[float] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Recherche dans le catalogue Sentinel Hub (STAC).
        
        Args:
            bbox: Bounding box {min_lon, min_lat, max_lon, max_lat}
            date_from: Date début (incluse)
            date_to: Date fin (incluse)
            sensor: 'sentinel-2' ou 'sentinel-1'
            cloud_cover_max: Cloud cover max % (override config)
            limit: Nombre max résultats
            
        Returns:
            {
                'type': 'FeatureCollection',
                'features': [
                    {
                        'id': product_id,
                        'properties': {
                            'datetime': ISO datetime,
                            'eo:cloud_cover': float,
                            'platform': 'Sentinel-2',
                            ...
                        },
                        'geometry': {...},
                        'links': [...]
                    },
                    ...
                ]
            }
        """
        log.info(f"Searching catalog: bbox={bbox}, dates={date_from} to {date_to}, sensor={sensor}")
        
        try:
            # Déterminer la collection de données
            if sensor == "sentinel-1":
                collection = "sentinel-1-grd"
            else:
                collection = "sentinel-2-l2a"
            
            cc_max = cloud_cover_max if cloud_cover_max is not None else self.max_cloud_cover
            
            # Construire les paramètres de recherche
            search_params = {
                "collections": [collection],
                "bbox": [bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"]],
                "datetime": f"{date_from.isoformat()}T00:00:00Z/{date_to.isoformat()}T23:59:59Z",
                "limit": limit,
            }
            
            # Ajouter filtre cloud cover si Sentinel-2
            if sensor == "sentinel-2":
                search_params["query"] = {
                    "eo:cloud_cover": {
                        "lte": cc_max
                    }
                }
            
            # Requête STAC Search
            headers = self._get_auth_headers()
            response = self.client.post(
                f"{self.api_url}/api/v1/catalog/search",
                json=search_params,
                headers=headers,
            )
            response.raise_for_status()
            
            result = response.json()
            log.info(f"Found {len(result.get('features', []))} products")
            
            return result
            
        except httpx.HTTPError as e:
            log.error(f"Catalog search failed: {e}")
            raise SentinelHubException(f"Catalog search error: {e}")

    def get_product_metadata(
        self,
        product_id: str,
    ) -> Dict[str, Any]:
        """
        Récupère les métadonnées complètes d'un produit.
        
        Args:
            product_id: ID du produit (ex: S2A_MSIL2A_...)
            
        Returns:
            Métadonnées STAC du produit
        """
        log.info(f"Fetching metadata for product {product_id}")
        
        try:
            headers = self._get_auth_headers()
            response = self.client.get(
                f"{self.api_url}/api/v1/catalog/search/{product_id}",
                headers=headers,
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            log.error(f"Failed to fetch metadata for {product_id}: {e}")
            raise SentinelHubException(f"Metadata fetch error: {e}")

    def submit_process_request(
        self,
        evalscript: str,
        bbox: Dict[str, float],
        date_from: date,
        date_to: date,
        sensor: str = "sentinel-2",
        response_type: str = "application/json",
    ) -> str:
        """
        Soumet une requête Process API (évaluation de script).
        
        Args:
            evalscript: Script d'évaluation JavaScript
            bbox: Bounding box
            date_from: Date début
            date_to: Date fin
            sensor: Type de capteur
            response_type: Type de réponse attendu
            
        Returns:
            job_id (pour polling)
        """
        log.info(f"Submitting process request for {sensor}")
        
        try:
            # Déterminer la collection
            collection = "sentinel-1-grd" if sensor == "sentinel-1" else "sentinel-2-l2a"
            
            payload = {
                "processRequest": {
                    "input": {
                        "bounds": {
                            "bbox": [bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"]],
                            "properties": [
                                {
                                    "name": "datetime",
                                    "operator": "between",
                                    "args": [date_from.isoformat(), date_to.isoformat()]
                                }
                            ]
                        },
                        "data": [
                            {
                                "type": collection,
                                "dataFilter": {} if sensor == "sentinel-1" else {"maxCloudCoverage": 50}
                            }
                        ]
                    },
                    "output": {
                        "responses": [
                            {
                                "identifier": "default",
                                "format": {
                                    "type": response_type
                                }
                            }
                        ]
                    },
                    "evalscript": evalscript
                }
            }
            
            headers = self._get_auth_headers()
            response = self.client.post(
                f"{self.api_url}/api/v1/process",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            
            # La réponse contient un job ID
            result = response.json()
            job_id = result.get("id") or result.get("jobId")
            
            log.info(f"Process request submitted: job_id={job_id}")
            return job_id
            
        except httpx.HTTPError as e:
            log.error(f"Process request submission failed: {e}")
            raise SentinelHubException(f"Process request error: {e}")

    def get_process_status(self, job_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un job Process API.
        
        Args:
            job_id: ID du job
            
        Returns:
            {
                'status': 'CREATED'|'QUEUED'|'RUNNING'|'DONE'|'ERROR'|'CANCELED',
                'progress': 0-100,
                'estimatedTime': int (ms),
                ...
            }
        """
        log.info(f"Fetching status for job {job_id}")
        
        try:
            headers = self._get_auth_headers()
            response = self.client.get(
                f"{self.api_url}/api/v1/process/{job_id}",
                headers=headers,
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            log.error(f"Failed to fetch job status: {e}")
            raise SentinelHubException(f"Job status error: {e}")

    def get_process_result(self, job_id: str) -> bytes:
        """
        Récupère le résultat d'un job (quand status=DONE).
        
        Args:
            job_id: ID du job
            
        Returns:
            Données brutes (JSON, image, etc.)
        """
        log.info(f"Fetching result for job {job_id}")
        
        try:
            headers = self._get_auth_headers()
            response = self.client.get(
                f"{self.api_url}/api/v1/process/{job_id}/result",
                headers=headers,
            )
            response.raise_for_status()
            
            return response.content
            
        except httpx.HTTPError as e:
            log.error(f"Failed to fetch job result: {e}")
            raise SentinelHubException(f"Job result error: {e}")

    def _get_auth_headers(self) -> Dict[str, str]:
        """Construit les headers d'authentification."""
        import base64
        
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def __del__(self):
        """Cleanup."""
        if hasattr(self, "client"):
            self.client.close()


class SentinelHubException(Exception):
    """Exception Sentinel Hub."""
    pass


def coordonnees_to_bbox(coordonnees: list[dict]) -> tuple[float, float, float, float]:
    """Convertit polygon [{lat, lon}, ...] en bbox (min_lon, min_lat, max_lon, max_lat).

    Sentinel Hub attend (west, south, east, north).
    Lève ValueError si la liste est vide ou mal formée.
    """
    if not coordonnees:
        raise ValueError("Coordonnées vides — impossible de calculer le bbox")
    lats = [c["lat"] for c in coordonnees]
    lons = [c["lon"] for c in coordonnees]
    if not lats or not lons:
        raise ValueError("Coordonnées mal formées — lat/lon manquants")
    return (min(lons), min(lats), max(lons), max(lats))


def get_evalscript_ndvi_ndre_ndmi() -> str:
    """
    Retourne un evalscript pour calculer NDVI, NDRE, NDMI.
    
    S2 Bands :
      - B02 (Blue, 490nm) = index 1
      - B03 (Green, 560nm) = index 2
      - B04 (Red, 665nm) = index 3
      - B05 (Red Edge 705nm) = index 4
      - B08 (NIR, 842nm) = index 7
      - B11 (SWIR 1610nm) = index 10
    """
    return """
//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04", "B05", "B08", "B11"],
    output: {
      bands: 3,
      sampleType: SampleType.FLOAT32
    }
  }
}

function evaluatePixel(sample) {
  // NDVI = (NIR - RED) / (NIR + RED)
  let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
  
  // NDRE = (NIR - RED_EDGE) / (NIR + RED_EDGE)
  let ndre = (sample.B08 - sample.B05) / (sample.B08 + sample.B05);
  
  // NDMI = (NIR - SWIR) / (NIR + SWIR)
  let ndmi = (sample.B08 - sample.B11) / (sample.B08 + sample.B11);
  
  return [ndvi, ndre, ndmi];
}
"""


def get_evalscript_savi_evi_msavi() -> str:
    """
    Retourne un evalscript pour calculer SAVI, EVI, MSAVI.
    """
    return """
//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04", "B08", "B11"],
    output: {
      bands: 3,
      sampleType: SampleType.FLOAT32
    }
  }
}

function evaluatePixel(sample) {
  // SAVI = ((NIR - RED) / (NIR + RED + L)) * (1 + L), avec L = 0.5
  let L = 0.5;
  let savi = ((sample.B08 - sample.B04) / (sample.B08 + sample.B04 + L)) * (1 + L);
  
  // EVI = 2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))
  let evi = 2.5 * ((sample.B08 - sample.B04) / (sample.B08 + 6 * sample.B04 - 7.5 * sample.B02 + 1));
  
  // MSAVI = (2 * NIR + 1 - sqrt((2 * NIR + 1)^2 - 8 * (NIR - RED))) / 2
  let msavi_inner = (2 * sample.B08 + 1) * (2 * sample.B08 + 1) - 8 * (sample.B08 - sample.B04);
  let msavi = (2 * sample.B08 + 1 - Math.sqrt(msavi_inner)) / 2;
  
  return [savi, evi, msavi];
}
"""
