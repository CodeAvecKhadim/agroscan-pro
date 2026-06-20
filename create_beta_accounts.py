"""
Script de création des comptes BÊTA TERRAIN officiels — AgroScan Pro.
Crée 10 bêta-testeurs (beta01…beta10) avec leurs PINs respectifs.
Exécuter depuis /opt/agroscan :
    python create_beta_accounts.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models import User, Organization, UserRole
from app.models.beta import BetaLog  # noqa: F401 — force table creation
from app.services.subscription import create_default_subscription
from app.models import Subscription, PlanType, SubStatus

# ── Assure que toutes les tables existent ─────────────────────────────────────
import app.models.beta  # noqa: F401
Base.metadata.create_all(bind=engine)

BETA_BADGE = "BÊTA TERRAIN AUTORISÉ"
BETA_PERMISSIONS = [
    "Mon Champ",
    "Cartographie GPS",
    "Santé des Cultures Pro",
    "Diagnostic Maladies",
    "Météo Agricole",
    "Polélé",
    "Rapports PDF",
]

COMPTES = [
    {"username": "beta01", "pin": "1001"},
    {"username": "beta02", "pin": "1002"},
    {"username": "beta03", "pin": "1003"},
    {"username": "beta04", "pin": "1004"},
    {"username": "beta05", "pin": "1005"},
    {"username": "beta06", "pin": "1006"},
    {"username": "beta07", "pin": "1007"},
    {"username": "beta08", "pin": "1008"},
    {"username": "beta09", "pin": "1009"},
    {"username": "beta10", "pin": "1010"},
]


def create_accounts():
    db = SessionLocal()
    created = []
    skipped = []

    try:
        for i, compte in enumerate(COMPTES, start=1):
            username = compte["username"]
            pin = compte["pin"]
            email = f"{username}@beta.agroscan"
            phone = f"+2210000000{i:02d}"

            # Skip if already exists
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                skipped.append(username)
                continue

            # Create organisation isolée pour ce testeur
            org = Organization(
                name=f"Bêta Terrain — {username}",
                is_cooperative=False,
            )
            db.add(org)
            db.flush()

            user = User(
                org_id=org.id,
                full_name=f"Bêta Testeur {username.upper()}",
                email=email,
                phone=phone,
                hashed_password=hash_password(pin),
                role=UserRole.PRODUCTEUR,
                profil="BETA_TESTEUR",
                is_active=True,
                email_verified=True,
                phone_verified=True,
                # Champs bêta
                is_beta=True,
                beta_badge=BETA_BADGE,
                beta_permissions=BETA_PERMISSIONS,
                beta_max_parcelles=1,
            )
            db.add(user)
            db.flush()

            # Abonnement gratuit, non-facturable, permanent
            sub = Subscription(
                org_id=org.id,
                plan=PlanType.GRATUIT,
                status=SubStatus.ACTIVE,
                current_period_end=None,
                seats=1,
                auto_renew=False,
                campaign_billing="beta",
            )
            db.add(sub)
            db.commit()
            db.refresh(user)

            created.append({
                "username": username,
                "email": email,
                "phone": phone,
                "pin": pin,
                "user_id": user.id,
                "org_id": org.id,
            })

    finally:
        db.close()

    return created, skipped


def verify_logins(created):
    from app.core.security import verify_password
    db = SessionLocal()
    results = []
    try:
        for c in created:
            user = db.query(User).filter(User.email == c["email"]).first()
            ok = user and verify_password(c["pin"], user.hashed_password)
            results.append({
                "username": c["username"],
                "email": c["email"],
                "login_ok": bool(ok),
                "is_beta": bool(user.is_beta) if user else False,
                "badge": user.beta_badge if user else None,
            })
    finally:
        db.close()
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("  AGROSCAN PRO — Création des comptes BÊTA TERRAIN")
    print("=" * 60)

    created, skipped = create_accounts()

    if skipped:
        print(f"\n[SKIP] Déjà existants : {', '.join(skipped)}")

    if created:
        print(f"\n[OK] {len(created)} compte(s) créé(s) :")
        print(f"  {'Compte':<10} {'Email':<28} {'Téléphone':<18} {'PIN'}")
        print("  " + "-" * 68)
        for c in created:
            print(f"  {c['username']:<10} {c['email']:<28} {c['phone']:<18} {c['pin']}")

    # Vérification connexions
    all_accounts = []
    db = SessionLocal()
    try:
        for compte in COMPTES:
            email = f"{compte['username']}@beta.agroscan"
            user = db.query(User).filter(User.email == email).first()
            if user:
                all_accounts.append({"email": email, "pin": compte["pin"], "username": compte["username"]})
    finally:
        db.close()

    print(f"\n[VÉRIF] Connexions pour {len(all_accounts)} compte(s) :")
    from app.core.security import verify_password
    db2 = SessionLocal()
    try:
        all_ok = True
        for a in all_accounts:
            user = db2.query(User).filter(User.email == a["email"]).first()
            ok = user and verify_password(a["pin"], user.hashed_password)
            status = "✓" if ok else "✗"
            print(f"  {status} {a['username']} ({a['email']}) — PIN {a['pin']}")
            if not ok:
                all_ok = False
    finally:
        db2.close()

    print()
    if all_ok and all_accounts:
        print("[SUCCESS] Tous les comptes bêta sont opérationnels.")
    else:
        print("[ERREUR] Certains comptes ont échoué la vérification.")

    print("\n" + "=" * 60)
    print("  RAPPORT FINAL")
    print("=" * 60)
    print(f"  Comptes créés    : {len(created)}")
    print(f"  Comptes ignorés  : {len(skipped)} (existaient déjà)")
    print(f"  Total opératifs  : {len(all_accounts)}")
    print(f"  Rôle             : BETA_TESTEUR")
    print(f"  Badge            : {BETA_BADGE}")
    print(f"  Max parcelles    : 1")
    print(f"  Plan             : GRATUIT (non facturable)")
    print(f"  Permissions      : {', '.join(BETA_PERMISSIONS)}")
    print("=" * 60)
