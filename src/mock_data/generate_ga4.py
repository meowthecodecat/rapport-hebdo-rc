"""
Generateur de donnees mock "façon export GA4 Data API" pour un marche.

Ce module ne fait AUCUN appel reseau : tout est genere avec un RNG seede
(reproductible) a partir des parametres de config/settings.py. La forme
du JSON produit (cles, types, granularite) est concue pour ressembler a
ce que renverrait un vrai appel `runReport` de la GA4 Data API, afin que
le reste du pipeline (jointure, highlights, rapport) n'ait rien a
changer le jour ou ce module est remplace par du reel.

MOCK -> REEL : remplacer `generate_ga4_dataset()` par un module qui
appelle `google.analytics.data_v1beta.BetaAnalyticsDataClient.run_report`
avec :
  - dimensions: date / pagePath / sessionDefaultChannelGroup
  - metrics: sessions / conversions / userEngagementDuration
  - dateRanges: current_week, previous_week, same_week_last_year
puis qui remappe les lignes retournees vers exactement ce meme schema
(summary / top_pages / traffic_sources / trend_6m).
"""

import random
from datetime import date

from config.settings import MARKETS, RNG_SEED, TRAFFIC_CHANNELS
from src.mock_data.products_catalog import ORPHAN_GA4_PAGE, products_for_ga4
from src.mock_data.rng_helpers import pct as _pct, delta_with_occasional_outlier as _delta_with_occasional_outlier
from src.utils.dates import build_period, iter_weeks_back, get_current_week_start

TREND_WEEKS = 26  # ~6 mois de recul


def _build_top_pages(rng: random.Random, total_sessions: int) -> list[dict]:
    pages = []

    # Pages non-produit (pas de SKU) : accueil, collection, page de marque.
    non_product_pages = [
        ("/", None, "Home", 0.20, (12, 22)),
        ("/collections/all", None, "Collection - All Products", 0.09, (18, 32)),
        ("/pages/our-story", None, "Our Story", 0.05, (25, 45)),
    ]
    for url, sku, _label, share, engagement_range in non_product_pages:
        sessions = round(total_sessions * share * rng.uniform(0.85, 1.15))
        pages.append({
            "url": url,
            "sku": sku,
            "sessions": sessions,
            "engagement_time_avg_sec": round(rng.uniform(*engagement_range), 1),
            "sessions_vs_lw_pct": _delta_with_occasional_outlier(rng),
            "sessions_vs_ly_pct": _delta_with_occasional_outlier(rng),
        })

    # Pages produit (PDP) : le reste du trafic, reparti avec des poids
    # aleatoires normalises (certains produits sont plus vus que d'autres).
    remaining_share = 1 - sum(p[3] for p in non_product_pages)
    catalog = products_for_ga4()
    weights = [rng.uniform(0.4, 1.6) for _ in catalog]
    weight_sum = sum(weights)

    for product, weight in zip(catalog, weights):
        share = remaining_share * (weight / weight_sum)
        sessions = round(total_sessions * share * rng.uniform(0.85, 1.15))
        pages.append({
            "url": f"/products/{product.slug}",
            "sku": product.sku,
            "sessions": max(sessions, 1),
            "engagement_time_avg_sec": round(rng.uniform(30, 78), 1),
            "sessions_vs_lw_pct": _delta_with_occasional_outlier(rng),
            "sessions_vs_ly_pct": _delta_with_occasional_outlier(rng),
        })

    # Page orpheline volontaire : trafic long-traine (SEO) vers un produit
    # discontinue, sans SKU Shopify actif -> alimente le cas d'echec de
    # mapping "page GA4 sans produit Shopify" dans le script de jointure.
    orphan_sessions = max(round(total_sessions * rng.uniform(0.006, 0.015)), 1)
    pages.append({
        "url": ORPHAN_GA4_PAGE["url"],
        "sku": ORPHAN_GA4_PAGE["sku"],
        "sessions": orphan_sessions,
        "engagement_time_avg_sec": round(rng.uniform(18, 32), 1),
        "sessions_vs_lw_pct": _delta_with_occasional_outlier(rng, outlier_chance=0.05),
        "sessions_vs_ly_pct": _delta_with_occasional_outlier(rng, outlier_chance=0.05),
    })

    # Pas de troncature arbitraire : le catalogue ne genere de toute facon
    # qu'un nombre borne de pages (accueil/collection/story + 1 PDP par
    # produit + la page orpheline). Tronquer ici couperait au hasard de
    # vraies pages produit et creerait de faux echecs de mapping cote join.
    pages.sort(key=lambda p: p["sessions"], reverse=True)
    return pages


def _build_traffic_sources(rng: random.Random, total_sessions: int, traffic_mix: dict) -> list[dict]:
    sources = []
    for channel in TRAFFIC_CHANNELS:
        share = traffic_mix.get(channel, 0.0)
        sessions = round(total_sessions * share * rng.uniform(0.90, 1.10))
        sources.append({
            "channel": channel,
            "sessions": sessions,
            "sessions_vs_lw_pct": _pct(rng, -14, 14),
        })

    # Corrige l'arrondi cumule sur le plus gros canal pour que la somme
    # des sessions par canal colle au total (comme dans un vrai export GA4).
    drift = total_sessions - sum(s["sessions"] for s in sources)
    sources.sort(key=lambda s: s["sessions"], reverse=True)
    sources[0]["sessions"] += drift

    # Garantit au moins un canal avec un ecart significatif vs LW, pour
    # que le bloc "Highlights" ait toujours matiere a commenter en demo.
    forced = rng.choice(sources[1:])
    forced["sessions_vs_lw_pct"] = rng.choice([-1, 1]) * round(rng.uniform(17, 32), 1)

    for s in sources:
        s["pct_of_total"] = round(100 * s["sessions"] / total_sessions, 1)

    sources.sort(key=lambda s: s["sessions"], reverse=True)
    return sources


def _backward_walk(end_value: int, n: int, rng: random.Random) -> list[int]:
    """Reconstruit une serie de `n` valeurs qui se termine pile sur
    `end_value`, en remontant le temps avec un bruit + une derive legere."""
    values = [0] * n
    values[-1] = end_value
    for i in range(n - 2, -1, -1):
        factor = rng.uniform(0.97, 1.03) * rng.uniform(0.90, 1.10)
        values[i] = max(1, round(values[i + 1] / factor))
    return values


def _build_trend_6m(rng: random.Random, current_week_start: date, anchor_sessions: int, anchor_sessions_ly: int) -> list[dict]:
    weeks = iter_weeks_back(current_week_start, TREND_WEEKS)
    current_series = _backward_walk(anchor_sessions, TREND_WEEKS, rng)
    ly_series = _backward_walk(anchor_sessions_ly, TREND_WEEKS, rng)
    return [
        {"week_start": w.isoformat(), "sessions": cur, "sessions_ly": ly}
        for w, cur, ly in zip(weeks, current_series, ly_series)
    ]


def generate_ga4_dataset(market_code: str, today: date | None = None) -> dict:
    cfg = MARKETS[market_code]
    rng = random.Random(RNG_SEED + cfg["seed_offset"] * 1000)

    period = build_period(today)
    current_week_start = get_current_week_start(today)

    total_sessions = round(cfg["base_sessions"] * rng.uniform(0.93, 1.07))
    sessions_vs_lw_pct = _pct(rng, -10, 14)
    sessions_vs_ly_pct = _pct(rng, -15, 15)
    conversion_rate = round(cfg["base_conversion_rate"] * rng.uniform(0.90, 1.10), 2)
    conversion_rate_vs_lw_pct = _pct(rng, -10, 10)
    conversion_rate_vs_ly_pct = _pct(rng, -10, 10)

    # Sessions "meme semaine annee derniere" implicite, deduite du delta
    # summary, pour que le dernier point de la courbe L6M vs LY soit
    # coherent avec le % affiche dans la scorecard.
    anchor_sessions_ly = round(total_sessions / (1 + sessions_vs_ly_pct / 100))

    return {
        "market": market_code,
        "period": period,
        "summary": {
            "sessions": total_sessions,
            "conversion_rate": conversion_rate,
            "sessions_vs_lw_pct": sessions_vs_lw_pct,
            "sessions_vs_ly_pct": sessions_vs_ly_pct,
            "conversion_rate_vs_lw_pct": conversion_rate_vs_lw_pct,
            "conversion_rate_vs_ly_pct": conversion_rate_vs_ly_pct,
        },
        "top_pages": _build_top_pages(rng, total_sessions),
        "traffic_sources": _build_traffic_sources(rng, total_sessions, cfg["traffic_mix"]),
        "trend_6m": _build_trend_6m(rng, current_week_start, total_sessions, anchor_sessions_ly),
    }
