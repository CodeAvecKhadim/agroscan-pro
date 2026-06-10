"""
Upload preuves (photos + vidéos) — Module GESTION DE FERME.
Interface isolée pour migration future S3/Cloudinary.
"""
import hashlib
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

UPLOAD_DIR = Path("/opt/agroscan/uploads/activites")

_MIME_PHOTO  = {"image/jpeg", "image/png", "image/webp"}
_MIME_VIDEO  = {"video/mp4", "video/quicktime", "video/webm"}
_MAX_PHOTO   = 8  * 1024 * 1024   # 8 Mo
_MAX_VIDEO   = 50 * 1024 * 1024   # 50 Mo
_MAX_DUREE_S = 180                 # 3 min


async def save_preuve(file: UploadFile) -> dict:
    """
    Valide et sauvegarde localement une photo ou vidéo.
    Retourne {type, filename, url, taille_ko, photo_meta}.
    Remplacer uniquement cette fonction pour migrer vers S3.
    """
    mime = file.content_type or ""
    is_photo = mime in _MIME_PHOTO
    is_video = mime in _MIME_VIDEO

    if not is_photo and not is_video:
        raise HTTPException(415, f"Format non supporté : {mime}. Acceptés : JPEG/PNG/WebP/MP4/MOV/WebM.")

    contenu = await file.read()
    if not contenu:
        raise HTTPException(400, "Fichier vide.")

    max_taille = _MAX_PHOTO if is_photo else _MAX_VIDEO
    if len(contenu) > max_taille:
        limit_mo = max_taille // (1024 * 1024)
        raise HTTPException(413, f"Fichier trop lourd (max {limit_mo} Mo).")

    ext      = _ext_from_mime(mime)
    filename = f"{uuid.uuid4().hex}{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / filename).write_bytes(contenu)

    sha256 = hashlib.sha256(contenu).hexdigest()

    return {
        "type":        "photo" if is_photo else "video",
        "filename":    filename,
        "url":         f"/uploads/activites/{filename}",
        "taille_ko":   len(contenu) // 1024,
        "photo_meta": {
            "mime_type":    mime,
            "taille_b":     len(contenu),
            "hash_sha256":  sha256,
            "original_name": file.filename,
        },
    }


def delete_preuve(filename: str) -> bool:
    chemin = UPLOAD_DIR / filename
    if chemin.exists():
        chemin.unlink()
        return True
    return False


def build_url(filename: str) -> str:
    return f"/uploads/activites/{filename}"


def _ext_from_mime(mime: str) -> str:
    return {
        "image/jpeg":       ".jpg",
        "image/png":        ".png",
        "image/webp":       ".webp",
        "video/mp4":        ".mp4",
        "video/quicktime":  ".mov",
        "video/webm":       ".webm",
    }.get(mime, ".bin")
