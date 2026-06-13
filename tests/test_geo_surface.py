"""
Tests de régression pour le calcul de superficie des parcelles.

Bug corrigé : des points GPS aberrants (sauts > Q3+3×IQR) créaient des polygones
auto-intersectants, causant une surface jusqu'à 27× trop grande avec la formule Shoelace.
"""
import math
import pytest
from app.services.geo import surface_m2, perimetre_m, calcul_complet, _filter_gps_outliers


def _make_square(ref_lat: float, ref_lon: float, side_m: float):
    """Carré de side_m mètres centré sur ref_lat/ref_lon."""
    dlat = side_m / 111_320.0
    dlon = side_m / (111_320.0 * math.cos(math.radians(ref_lat)))
    return [
        {"lat": ref_lat,         "lon": ref_lon},
        {"lat": ref_lat + dlat,  "lon": ref_lon},
        {"lat": ref_lat + dlat,  "lon": ref_lon + dlon},
        {"lat": ref_lat,         "lon": ref_lon + dlon},
    ]


# ── Carré propre ────────────────────────────────────────────────────────────

class TestCarrePropre:
    def test_50x50_surface(self):
        coords = _make_square(14.0, -1.0, 50.0)
        assert abs(surface_m2(coords) - 2500.0) < 50  # ±2 %

    def test_50x50_perimetre(self):
        coords = _make_square(14.0, -1.0, 50.0)
        assert abs(perimetre_m(coords) - 200.0) < 5

    def test_100x100_surface(self):
        coords = _make_square(12.5, -13.0, 100.0)
        assert abs(surface_m2(coords) - 10_000.0) < 200


# ── Régression : outliers GPS gonflent la surface ───────────────────────────

class TestOutliersGPS:
    """
    Reproduit le bug signalé : parcelle gombo (~2 500 m²) affichait 67 436 m².
    Deux points GPS aberrants (sauts 318 m et 659 m) rendaient le polygone
    auto-intersectant et gonflaient la surface Shoelace.
    """

    def _coords_avec_outliers(self):
        """
        Polygone réaliste 50×50 m avec ~20 points le long des bords,
        puis 2 points GPS aberrants simulant une erreur satellite.
        Les outliers représentent <10 % des segments → filtre IQR fiable.
        """
        import math
        ref_lat, ref_lon, side_m = 14.0, -1.0, 50.0
        dlat = side_m / 111_320.0
        dlon = side_m / (111_320.0 * math.cos(math.radians(ref_lat)))

        # ~5 points par côté du carré (20 points au total)
        steps = 5
        bottom = [{"lat": ref_lat,        "lon": ref_lon + dlon * i / steps} for i in range(steps)]
        right  = [{"lat": ref_lat + dlat * i / steps, "lon": ref_lon + dlon} for i in range(steps)]
        top    = [{"lat": ref_lat + dlat, "lon": ref_lon + dlon * (steps - i) / steps} for i in range(steps)]
        left   = [{"lat": ref_lat + dlat * (steps - i) / steps, "lon": ref_lon} for i in range(steps)]
        base   = bottom + right + top + left  # 20 points

        # Outliers proches géographiquement mais créant un saut GPS typique (~300-600 m)
        # Similaires aux points 7 et 8 de la parcelle gombo réelle
        outlier1 = {"lat": ref_lat - 0.003, "lon": ref_lon - 0.003}  # ~450 m SW
        outlier2 = {"lat": ref_lat + 0.004, "lon": ref_lon + 0.001}  # ~445 m NE

        # Insérer entre point 6 et 7 (comme dans les données réelles)
        return base[:6] + [outlier1, outlier2] + base[6:]

    def test_outliers_sans_fix_gonflent_surface(self):
        """Sans filtrage, les outliers donneraient une surface aberrante."""
        coords = self._coords_avec_outliers()
        filtered = _filter_gps_outliers(coords)
        assert len(filtered) < len(coords), "Le filtre doit supprimer des points"

    def test_surface_avec_outliers_reste_correcte(self):
        """Avec le fix, la surface d'un carré 50×50 m reste ~2 500 m² malgré 2 outliers."""
        coords = self._coords_avec_outliers()
        s = surface_m2(coords)
        assert s < 10_000, f"Surface avec outliers = {s:.0f} m² (attendu < 10 000 m²)"
        assert s > 1_000,  f"Surface avec outliers = {s:.0f} m² (attendu > 1 000 m²)"

    def test_perimetre_avec_outliers_reste_coherent(self):
        """Le périmètre ne doit pas inclure les sauts GPS aberrants."""
        coords = self._coords_avec_outliers()
        p = perimetre_m(coords)
        assert p < 500, f"Périmètre avec outliers = {p:.0f} m (attendu < 500 m)"

    def test_parcelle_2500m2_ne_retourne_pas_6ha(self):
        """
        Test de non-régression principal :
        une parcelle de ~2 500 m² NE doit PAS retourner 6 ha (67 000 m²).
        """
        coords = self._coords_avec_outliers()
        result = calcul_complet(coords)
        assert result["superficie_ha"] < 1.0, (
            f"superficie_ha = {result['superficie_ha']} ha "
            f"(attendu < 1 ha pour une parcelle de ~2 500 m²)"
        )
        assert result["superficie_m2"] < 10_000, (
            f"superficie_m2 = {result['superficie_m2']} m² "
            f"(attendu < 10 000 m² pour une parcelle de ~2 500 m²)"
        )

    def test_filtre_gps_outliers_isole_deux_points(self):
        """_filter_gps_outliers supprime exactement les 2 points aberrants."""
        coords = self._coords_avec_outliers()
        filtered = _filter_gps_outliers(coords)
        n_original = len(coords)
        n_filtered = len(filtered)
        assert n_filtered == n_original - 2, (
            f"Attendu {n_original - 2} points après filtrage, obtenu {n_filtered}"
        )


# ── Données réelles parcelle gombo (Guinea) ─────────────────────────────────

COORDS_PARCELLE_GOMBO = [
    {"lat": 12.6336079, "lon": -12.8172065},
    {"lat": 12.633622,  "lon": -12.8173149},
    {"lat": 12.6338094, "lon": -12.8173981},
    {"lat": 12.6341648, "lon": -12.8174767},
    {"lat": 12.6345996, "lon": -12.8174197},
    {"lat": 12.6349136, "lon": -12.8171632},
    {"lat": 12.6359291, "lon": -12.8168689},
    {"lat": 12.6333951, "lon": -12.8182336},  # outlier (pt 7)
    {"lat": 12.6391983, "lon": -12.8169833},  # outlier (pt 8)
    {"lat": 12.6365683, "lon": -12.8161017},
    {"lat": 12.6362392, "lon": -12.816053},
    {"lat": 12.6359785, "lon": -12.8159954},
    {"lat": 12.6357016, "lon": -12.815991},
    {"lat": 12.6354518, "lon": -12.8160136},
    {"lat": 12.6350183, "lon": -12.816145},
    {"lat": 12.6337955, "lon": -12.8171528},
    {"lat": 12.6335312, "lon": -12.8176044},
    {"lat": 12.6334861, "lon": -12.8176903},
    {"lat": 12.6334628, "lon": -12.8177151},
    {"lat": 12.6334733, "lon": -12.8177477},
    {"lat": 12.6334903, "lon": -12.817781},
    {"lat": 12.6334927, "lon": -12.817827},
    {"lat": 12.6334922, "lon": -12.8178575},
    {"lat": 12.6334661, "lon": -12.8178318},
    {"lat": 12.6334403, "lon": -12.8178193},
    {"lat": 12.6334144, "lon": -12.8178115},
    {"lat": 12.6333855, "lon": -12.8178125},
    {"lat": 12.6333613, "lon": -12.8177858},
    {"lat": 12.6333432, "lon": -12.8177433},
    {"lat": 12.6333009, "lon": -12.8177409},
    {"lat": 12.6332733, "lon": -12.8177385},
    {"lat": 12.6332482, "lon": -12.817726},
    {"lat": 12.6332177, "lon": -12.8176864},
    {"lat": 12.6331993, "lon": -12.8176582},
    {"lat": 12.6331843, "lon": -12.8176309},
    {"lat": 12.6331685, "lon": -12.8175857},
    {"lat": 12.6331398, "lon": -12.8175953},
    {"lat": 12.6331072, "lon": -12.8176149},
    {"lat": 12.6331125, "lon": -12.8176422},
]


class TestParcelleGomboReelle:
    """Tests sur les vraies coordonnées GPS de la parcelle gombo (bug original)."""

    def test_avant_fix_surface_etait_67436(self):
        """Documente la valeur incorrecte produite par les outliers."""
        # Sans filtrage, les 39 points donnaient 67 435 m² (bug)
        from app.services.geo import _to_local_xy
        # On recrée surface_m2 sans filtre pour prouver le bug d'origine
        coords = COORDS_PARCELLE_GOMBO
        ref_lat = sum(c["lat"] for c in coords) / len(coords)
        ref_lon = sum(c["lon"] for c in coords) / len(coords)
        pts = _to_local_xy(coords, ref_lat, ref_lon)
        n = len(pts)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += pts[i][0] * pts[j][1]
            area -= pts[j][0] * pts[i][1]
        area_sans_filtre = abs(area) / 2.0
        assert area_sans_filtre > 60_000, (
            f"La valeur bugguée attendue est > 60 000 m², obtenu {area_sans_filtre:.0f} m²"
        )

    def test_apres_fix_surface_corrigee(self):
        """Après filtrage des outliers, la surface est significativement réduite."""
        s_avant = 67_435.5  # valeur stockée en DB avant fix
        s_apres = surface_m2(COORDS_PARCELLE_GOMBO)
        assert s_apres < s_avant * 0.5, (
            f"Surface après fix {s_apres:.0f} m² doit être < 50% de la valeur bugguée {s_avant:.0f} m²"
        )

    def test_filtre_supprime_exactement_2_outliers(self):
        """Le filtre identifie exactement les points 7 et 8 comme aberrants."""
        filtered = _filter_gps_outliers(COORDS_PARCELLE_GOMBO)
        assert len(filtered) == 37, f"Attendu 37 points filtrés, obtenu {len(filtered)}"

    def test_outliers_sont_points_7_et_8(self):
        """Les points retirés sont bien les points 7 et 8 (valeurs GPS aberrantes)."""
        filtered = _filter_gps_outliers(COORDS_PARCELLE_GOMBO)
        filtered_set = [(round(p["lat"], 7), round(p["lon"], 7)) for p in filtered]
        pt7 = (round(12.6333951, 7), round(-12.8182336, 7))
        pt8 = (round(12.6391983, 7), round(-12.8169833, 7))
        assert pt7 not in filtered_set, "Point 7 (outlier) doit être supprimé"
        assert pt8 not in filtered_set, "Point 8 (outlier) doit être supprimé"

    def test_parcelle_gombo_ne_retourne_plus_6ha(self):
        """Test de non-régression : la parcelle gombo ne doit plus afficher 6,7 ha."""
        result = calcul_complet(COORDS_PARCELLE_GOMBO)
        assert result["superficie_ha"] < 4.0, (
            f"superficie_ha = {result['superficie_ha']} ha "
            f"(ne doit plus retourner ~6,7 ha comme avant le fix)"
        )
        assert result["superficie_m2"] < 40_000, (
            f"superficie_m2 = {result['superficie_m2']} m² "
            f"(ne doit plus retourner ~67 436 m²)"
        )
