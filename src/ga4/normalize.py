"""
Normalise les reponses GA4 Data API (runReport) vers le schema canonique
consomme par join / highlights / build-report.

MOCK -> REEL : ce fichier ne change pas. Seule la provenance du bundle
(fixtures vs BetaAnalyticsDataClient) change.
"""

from __future__ import annotations

from datetime import date, timedelta

from src.mock_data.products_catalog import PRODUCTS


def _sku_by_product_path() -> dict[str, str]:
    """Map /products/<slug> -> SKU (meme regle qu'en prod)."""
    return {f"/products/{p.slug}": p.sku for p in PRODUCTS}


def _rows(report: dict) -> list[dict]:
    return report.get("rows") or []


def _dim(row: dict, index: int) -> str:
    return row["dimensionValues"][index]["value"]


def _metric(row: dict, index: int) -> float:
    return float(row["metricValues"][index]["value"])


def _metric_int(row: dict, index: int) -> int:
    return int(round(_metric(row, index)))


def _pct_delta(current: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return round(100.0 * (current - baseline) / baseline, 1)


def _parse_summary(report: dict) -> dict:
    """
    Fixture summary : 1 ligne, metrics =
      [0] sessions_cw, [1] sessions_lw, [2] sessions_ly,
      [3] cvr_cw, [4] cvr_lw, [5] cvr_ly
    (cvr en ratio 0-1 comme GA4 sessionConversionRate).
    """
    rows = _rows(report)
    if not rows:
        raise ValueError("Rapport summary GA4 vide.")
    row = rows[0]
    sessions = _metric_int(row, 0)
    sessions_lw = _metric_int(row, 1)
    sessions_ly = _metric_int(row, 2)
    cvr = round(_metric(row, 3) * 100, 2)  # -> % pour le rapport
    cvr_lw = _metric(row, 4) * 100
    cvr_ly = _metric(row, 5) * 100
    return {
        "sessions": sessions,
        "conversion_rate": cvr,
        "sessions_vs_lw_pct": _pct_delta(sessions, sessions_lw),
        "sessions_vs_ly_pct": _pct_delta(sessions, sessions_ly),
        "conversion_rate_vs_lw_pct": _pct_delta(cvr, cvr_lw),
        "conversion_rate_vs_ly_pct": _pct_delta(cvr, cvr_ly),
    }


def _parse_top_pages(report: dict) -> list[dict]:
    """
    dimensions: pagePath
    metrics: sessions, averageSessionDuration, sessionsLw, sessionsLy
    """
    sku_by_path = _sku_by_product_path()
    pages = []
    for row in _rows(report):
        url = _dim(row, 0)
        sessions = _metric_int(row, 0)
        engagement = round(_metric(row, 1), 1)
        sessions_lw = _metric_int(row, 2)
        sessions_ly = _metric_int(row, 3)
        # SKU : extrait du path produit, sinon None (home/collection/...).
        # Les pages orphelines (produit discontinue) peuvent porter un
        # custom dimension sku dans la fixture via dimension[1] optionnel ;
        # sinon on tente le catalogue, puis un fallback depuis un suffixe.
        sku = sku_by_path.get(url)
        dims = row.get("dimensionValues") or []
        if sku is None and len(dims) > 1 and dims[1].get("value"):
            sku = dims[1]["value"]
            if sku in ("(not set)", ""):
                sku = None
        pages.append({
            "url": url,
            "sku": sku,
            "sessions": sessions,
            "engagement_time_avg_sec": engagement,
            "sessions_vs_lw_pct": _pct_delta(sessions, sessions_lw),
            "sessions_vs_ly_pct": _pct_delta(sessions, sessions_ly),
        })
    pages.sort(key=lambda p: p["sessions"], reverse=True)
    return pages


def _parse_traffic_sources(report: dict) -> list[dict]:
    """
    dimensions: sessionDefaultChannelGroup
    metrics: sessions, sessionsLw
    """
    sources = []
    for row in _rows(report):
        sessions = _metric_int(row, 0)
        sessions_lw = _metric_int(row, 1)
        sources.append({
            "channel": _dim(row, 0),
            "sessions": sessions,
            "sessions_vs_lw_pct": _pct_delta(sessions, sessions_lw),
        })

    total = sum(s["sessions"] for s in sources) or 1
    for s in sources:
        s["pct_of_total"] = round(100.0 * s["sessions"] / total, 1)
    sources.sort(key=lambda s: s["sessions"], reverse=True)
    return sources


def _parse_trend_6m(report: dict, week_start: date) -> list[dict]:
    """
    dimensions: weekStart (YYYY-MM-DD, lundi)
    metrics: sessions, sessionsLy

    Si les fixtures n'ont pas de dimension date explicite, on aligne les
    lignes sur les 26 semaines qui se terminent a `week_start`.
    """
    rows = _rows(report)
    points = []
    for i, row in enumerate(rows):
        dims = row.get("dimensionValues") or []
        if dims and dims[0].get("value"):
            ws = dims[0]["value"]
        else:
            ws = (week_start - timedelta(days=7 * (len(rows) - 1 - i))).isoformat()
        points.append({
            "week_start": ws,
            "sessions": _metric_int(row, 0),
            "sessions_ly": _metric_int(row, 1),
        })
    points.sort(key=lambda p: p["week_start"])
    return points


def normalize_ga4_bundle(
    market_code: str,
    period: dict,
    week_start: date,
    bundle: dict[str, dict],
) -> dict:
    required = ("summary", "top_pages", "traffic_sources", "trend_6m")
    missing = [k for k in required if k not in bundle]
    if missing:
        raise KeyError(f"Bundle GA4 incomplet pour {market_code}: manque {missing}")

    return {
        "market": market_code,
        "period": period,
        "source": "ga4",
        "summary": _parse_summary(bundle["summary"]),
        "top_pages": _parse_top_pages(bundle["top_pages"]),
        "traffic_sources": _parse_traffic_sources(bundle["traffic_sources"]),
        "trend_6m": _parse_trend_6m(bundle["trend_6m"], week_start),
    }
