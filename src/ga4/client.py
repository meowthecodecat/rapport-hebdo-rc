"""
Fabrique du client GA4 + orchestration fetch -> schema canonique.

Le reste du pipeline (join, rapport) ne parle jamais au client directement :
il consomme uniquement le dict canonique ecrit dans data/raw/ga4_*.json.
"""

from __future__ import annotations

from datetime import date

from config.settings import GA4_MODE, MARKETS
from src.ga4.mock_client import MockGa4Client
from src.ga4.normalize import normalize_ga4_bundle
from src.ga4.real_client import RealGa4Client
from src.utils.dates import build_period, get_current_week_start


def get_ga4_client():
    """Retourne le client actif selon GA4_MODE (mock | real)."""
    if GA4_MODE == "mock":
        return MockGa4Client()
    if GA4_MODE == "real":
        return RealGa4Client()
    raise ValueError(f"GA4_MODE invalide: {GA4_MODE!r}. Utiliser 'mock' ou 'real'.")


def fetch_canonical_ga4(market_code: str, today: date | None = None) -> dict:
    """
    Charge les 4 rapports GA4 (fixtures ou API), puis normalise vers
    le schema canonique attendu par join / build-report.
    """
    if market_code not in MARKETS:
        raise KeyError(f"Marche inconnu: {market_code}")

    period = build_period(today)
    week_start = get_current_week_start(today)
    client = get_ga4_client()
    bundle = client.fetch_reports(market_code, period)
    return normalize_ga4_bundle(
        market_code=market_code,
        period=period,
        week_start=week_start,
        bundle=bundle,
    )
