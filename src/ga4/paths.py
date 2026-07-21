"""Chemins des fixtures GA4 (faux rapports Data API)."""

from pathlib import Path

from src.utils.io import REPO_ROOT

# Fixtures versionnees : ce sont les "faux rapports GA4" de la PoC.
# Contrairement a data/raw/, elles sont committees et editables a la main.
FIXTURES_ROOT = REPO_ROOT / "data" / "fixtures" / "ga4"

REPORT_NAMES = (
    "summary",
    "top_pages",
    "traffic_sources",
    "trend_6m",
)


def fixtures_dir(market: str) -> Path:
    return FIXTURES_ROOT / market.lower()


def fixture_path(market: str, report_name: str) -> Path:
    if report_name not in REPORT_NAMES:
        raise ValueError(f"Rapport GA4 inconnu: {report_name!r}. Attendu: {REPORT_NAMES}")
    return fixtures_dir(market) / f"{report_name}.json"
