#!/usr/bin/env bash
# Démarrage rapide d'AgroScan Pro
python -m venv .venv 2>/dev/null
source .venv/bin/activate 2>/dev/null
pip install -r requirements.txt -q
cp -n .env.example .env 2>/dev/null
echo "Lancement sur http://localhost:8000"
uvicorn app.main:app --reload
