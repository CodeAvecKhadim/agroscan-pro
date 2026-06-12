"""
Service upload photos — abstraction stockage local.
Interface isolée pour migration future S3/Cloudinary sans toucher la logique métier.
"""
import hashlib
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException

BASE_UPLOAD = Path("/opt/agroscan/uploads")

_SOUS_DOSSIERS = {
    "maladie":      BASE_UPLOAD / "maladies",
    "ravageur":     BASE_UPLOAD / "ravageurs",
    "parcelle":     BASE_UPLOAD / "parcelles",
    "activite":     BASE_UPLOAD / "activites",
    "rapport":      BASE_UPLOAD / "rapports",
    "observation":  BASE_UPLOAD / "observations",
}

_MIME_AUTORISE = {"image/jpeg", "image/png", "image/webp"}
_MAX_TAILLE    = 8 * 1024 * 1024   # 8 Mo


async def save_photo(file: UploadFile, type_upload: str) -> dict:
    """
    Sauvegarde une photo localement.
    Retourne {filename, url, taille_ko, metadata}.
    Remplacer uniquement cette fonction pour migrer vers S3.
    """
    if type_upload not in _SOUS_DOSSIERS:
        raise HTTPException(400, f"type_upload invalide : {type_upload}")

    contenu = await file.read()
    if not contenu:
        raise HTTPException(400, "Fichier vide.")
    if len(contenu) > _MAX_TAILLE:
        raise HTTPException(413, "Photo trop lourde (max 8 Mo).")

    mime = file.content_type or ""
    if mime not in _MIME_AUTORISE:
        raise HTTPException(415, f"Format non supporté : {mime}. Acceptés : JPEG, PNG, WebP.")

    ext      = _ext_from_mime(mime)
    filename = f"{uuid.uuid4().hex}{ext}"
    dossier  = _SOUS_DOSSIERS[type_upload]
    dossier.mkdir(parents=True, exist_ok=True)
    chemin   = dossier / filename

    chemin.write_bytes(contenu)

    sha256 = hashlib.sha256(contenu).hexdigest()

    return {
        "filename":      filename,
        "url":           build_url(filename, type_upload),
        "thumbnail_url": None,
        "taille_ko":     len(contenu) // 1024,
        "metadata": {
            "mime_type":  mime,
            "taille_b":   len(contenu),
            "hash_sha256": sha256,
            "original_name": file.filename,
        },
    }


def build_url(filename: str, type_upload: str) -> str:
    """URL publique locale. À remplacer par CDN URL lors de la migration."""
    sous_dossier = _SOUS_DOSSIERS[type_upload].name
    return f"/uploads/{sous_dossier}/{filename}"


def delete_photo(filename: str, type_upload: str) -> bool:
    """Supprime physiquement un fichier. Retourne True si supprimé."""
    chemin = _SOUS_DOSSIERS.get(type_upload, BASE_UPLOAD) / filename
    if chemin.exists():
        chemin.unlink()
        return True
    return False


def _ext_from_mime(mime: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png":  ".png",
        "image/webp": ".webp",
    }.get(mime, ".jpg")
