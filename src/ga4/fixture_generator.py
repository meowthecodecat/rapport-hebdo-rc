"""
Genere de faux rapports GA4 au format Data API `runReport`.

Ces fichiers (data/fixtures/ga4/<market>/*.json) sont la matiere premiere
de la PoC : editables a la main, versionnables, et remplacables plus tard
par de vrais dumps d'API sans toucher au normalizer.

On reutilise la logique de volumetrie de src/mock_data/generate_ga4.py
pour garder des ordres de grandeur plausibles, puis on "emballe" le tout
dans la forme dimensionHeaders / metricHeaders / rows de GA4.
"""

from __future__ import annotations

from datetime import date

from config.settings import ALL_MARKETS, GA4_PROPERTY_IDS
from src.ga4.paths import fixture_path, fixtures_dir
from src.mock_data.generate_ga4 import generate_ga4_dataset
from src.utils.io import write_json


def _run_report(
    *,
    dimension_headers: list[str],
    metric_headers: list[tuple[str, str]],
    rows: list[dict],
    property_id: str,
    notes: str,
) -> dict:
    """Construit un payload proche d'une reponse `RunReportResponse` serialisee."""
    return {
        "kind": "analyticsData#runReport",
        "property": property_id,
        "notes": notes,
        "dimensionHeaders": [{"name": name} for name in dimension_headers],
        "metricHeaders": [
            {"name": name, "type": mtype} for name, mtype in metric_headers
        ],
        "rows": rows,
        "rowCount": len(rows),
        "metadata": {"currencyCode": "USD", "timeZone": "Europe/Paris"},
    }


def _row(dims: list[str], metrics: list[str | int | float]) -> dict:
    return {
        "dimensionValues": [{"value": d} for d in dims],
        "metricValues": [{"value": str(m)} for m in metrics],
    }


def _cvr_ratio(pct: float) -> str:
    """Conversion rate canonique en % -> ratio GA4 (0-1)."""
    return f"{pct / 100:.6f}"


def canonical_to_api_fixtures(canonical: dict, property_id: str) -> dict[str, dict]:
    """Inverse du normalizer : schema canonique -> 4 faux runReport."""
    summary = canonical["summary"]

    # Reconstitue les baselines a partir des % vs LW / vs LY.
    sessions = summary["sessions"]
    sessions_lw = round(sessions / (1 + summary["sessions_vs_lw_pct"] / 100))
    sessions_ly = round(sessions / (1 + summary["sessions_vs_ly_pct"] / 100))
    cvr = summary["conversion_rate"]
    cvr_lw = cvr / (1 + summary["conversion_rate_vs_lw_pct"] / 100)
    cvr_ly = cvr / (1 + summary["conversion_rate_vs_ly_pct"] / 100)

    summary_report = _run_report(
        dimension_headers=[],
        metric_headers=[
            ("sessions", "TYPE_INTEGER"),
            ("sessionsLw", "TYPE_INTEGER"),
            ("sessionsLy", "TYPE_INTEGER"),
            ("sessionConversionRate", "TYPE_FLOAT"),
            ("sessionConversionRateLw", "TYPE_FLOAT"),
            ("sessionConversionRateLy", "TYPE_FLOAT"),
        ],
        rows=[
            _row(
                [],
                [
                    sessions,
                    sessions_lw,
                    sessions_ly,
                    _cvr_ratio(cvr),
                    _cvr_ratio(cvr_lw),
                    _cvr_ratio(cvr_ly),
                ],
            )
        ],
        property_id=property_id,
        notes=(
            "PoC fixture: 1 row, 3 periodes (CW/LW/LY) aplaties en metrics. "
            "En prod, preferer 3 dateRanges sur un vrai runReport."
        ),
    )

    page_rows = []
    for page in canonical["top_pages"]:
        sessions_p = page["sessions"]
        sessions_lw_p = round(sessions_p / (1 + page["sessions_vs_lw_pct"] / 100))
        sessions_ly_p = round(sessions_p / (1 + page["sessions_vs_ly_pct"] / 100))
        dims = [page["url"]]
        # Dimension optionnelle sku (custom) pour les pages hors catalogue
        # (orpheline discontinue) : le normalizer la relit si presente.
        if page.get("sku"):
            dims.append(page["sku"])
        else:
            dims.append("(not set)")
        page_rows.append(
            _row(
                dims,
                [
                    sessions_p,
                    page["engagement_time_avg_sec"],
                    max(sessions_lw_p, 1),
                    max(sessions_ly_p, 1),
                ],
            )
        )

    top_pages_report = _run_report(
        dimension_headers=["pagePath", "customEvent:sku"],
        metric_headers=[
            ("sessions", "TYPE_INTEGER"),
            ("averageSessionDuration", "TYPE_SECONDS"),
            ("sessionsLw", "TYPE_INTEGER"),
            ("sessionsLy", "TYPE_INTEGER"),
        ],
        rows=page_rows,
        property_id=property_id,
        notes=(
            "PoC fixture: pagePath + sku custom. En prod, le sku peut etre "
            "derive du pagePath (/products/<slug>) sans custom dimension."
        ),
    )

    source_rows = []
    for src in canonical["traffic_sources"]:
        sessions_s = src["sessions"]
        sessions_lw_s = round(sessions_s / (1 + src["sessions_vs_lw_pct"] / 100))
        source_rows.append(
            _row(
                [src["channel"]],
                [sessions_s, max(sessions_lw_s, 0)],
            )
        )

    traffic_report = _run_report(
        dimension_headers=["sessionDefaultChannelGroup"],
        metric_headers=[
            ("sessions", "TYPE_INTEGER"),
            ("sessionsLw", "TYPE_INTEGER"),
        ],
        rows=source_rows,
        property_id=property_id,
        notes="PoC fixture: channel group + sessions CW/LW.",
    )

    trend_rows = [
        _row([point["week_start"]], [point["sessions"], point["sessions_ly"]])
        for point in canonical["trend_6m"]
    ]
    trend_report = _run_report(
        dimension_headers=["weekStart"],
        metric_headers=[
            ("sessions", "TYPE_INTEGER"),
            ("sessionsLy", "TYPE_INTEGER"),
        ],
        rows=trend_rows,
        property_id=property_id,
        notes=(
            "PoC fixture: serie hebdo L6M. En prod, dimension `date` (YYYYMMDD) "
            "agregée par semaine ISO cote normalizer."
        ),
    )

    return {
        "summary": summary_report,
        "top_pages": top_pages_report,
        "traffic_sources": traffic_report,
        "trend_6m": trend_report,
    }


def generate_fixtures_for_market(market_code: str, today: date | None = None) -> list[str]:
    """Genere et ecrit les 4 fixtures runReport pour un marche. Retourne les paths."""
    canonical = generate_ga4_dataset(market_code, today=today)
    property_id = GA4_PROPERTY_IDS.get(market_code, f"properties/MOCK-{market_code}")
    bundle = canonical_to_api_fixtures(canonical, property_id)

    written: list[str] = []
    fixtures_dir(market_code).mkdir(parents=True, exist_ok=True)
    for name, payload in bundle.items():
        path = fixture_path(market_code, name)
        write_json(path, payload)
        written.append(str(path))
    return written


def generate_all_fixtures(today: date | None = None) -> dict[str, list[str]]:
    return {market: generate_fixtures_for_market(market, today=today) for market in ALL_MARKETS}
