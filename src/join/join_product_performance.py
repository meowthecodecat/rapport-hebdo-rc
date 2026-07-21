"""
Jointure Produit : croise Shopify (units, net sales) et GA4 (trafic PDP,
conversion) via le SKU, pour les marches e-commerce uniquement (US/UK).

En prod, cette jointure est le point le plus fragile du pipeline : un
produit peut ne pas avoir de page dediee trackee, un slug d'URL peut
diverger du SKU, une page peut survivre a un produit retire du
catalogue... Ce script ne masque jamais ces cas : il les isole dans un
log de mapping dedie (data/processed/mapping_log_<market>.json) et les
imprime clairement sur la sortie standard, pour qu'ils soient traites
manuellement plutot que silencieusement ignores.

MOCK -> REEL : la logique de jointure ci-dessous ne change pas. Seuls
`generate_ga4_dataset`/`generate_shopify_dataset` en amont seraient
remplaces par de vrais appels API - le join continue de lire les memes
fichiers data/raw/ga4_<market>.json et data/raw/shopify_<market>.json
(ou directement les payloads en memoire si le pipeline devient temps reel).
"""

from datetime import datetime, timezone

from config.settings import ECOMMERCE_MARKETS
from src.utils.io import ga4_path, shopify_path, join_path, mapping_log_path, read_json, write_json

REASON_SHOPIFY_WITHOUT_GA4 = (
    "Aucune page produit GA4 trouvee pour ce SKU. A verifier manuellement : "
    "page non trackee, slug d'URL divergent du SKU, ou produit vendu hors "
    "du site (retail, marketplace) sans PDP dediee."
)
REASON_GA4_WITHOUT_SHOPIFY = (
    "Page produit GA4 trackee sans SKU Shopify correspondant. A verifier "
    "manuellement : produit retire du catalogue, slug d'URL obsolete, ou "
    "page de test/preview restee indexee."
)


def _sessions_conversion(orders: int, sessions: int) -> float:
    if sessions <= 0:
        return 0.0
    return round(100 * orders / sessions, 2)


def join_market(market_code: str) -> dict:
    if market_code not in ECOMMERCE_MARKETS:
        raise ValueError(
            f"{market_code} n'est pas un marche e-commerce : rien a joindre "
            f"(pas de dataset Shopify pour ce marche)."
        )

    ga4 = read_json(ga4_path(market_code))
    shopify = read_json(shopify_path(market_code))

    ga4_pages_by_sku = {p["sku"]: p for p in ga4["top_pages"] if p["sku"]}
    shopify_products_by_sku = {p["sku"]: p for p in shopify["products"]}

    matched_skus = set(ga4_pages_by_sku) & set(shopify_products_by_sku)
    unmatched_shopify_skus = set(shopify_products_by_sku) - set(ga4_pages_by_sku)
    unmatched_ga4_skus = set(ga4_pages_by_sku) - set(shopify_products_by_sku)

    joined = []
    for sku in matched_skus:
        page = ga4_pages_by_sku[sku]
        product = shopify_products_by_sku[sku]
        joined.append({
            "sku": sku,
            "product_name": product["product_name"],
            "category": product["category"],
            "url": page["url"],
            "sessions": page["sessions"],
            "engagement_time_avg_sec": page["engagement_time_avg_sec"],
            "sessions_vs_lw_pct": page["sessions_vs_lw_pct"],
            "orders": product["orders"],
            "units": product["units"],
            "net_sales": product["net_sales"],
            "units_vs_lw_pct": product["units_vs_lw_pct"],
            "net_sales_vs_lw_pct": product["net_sales_vs_lw_pct"],
            "conversion_rate_pct": _sessions_conversion(product["orders"], page["sessions"]),
        })
    joined.sort(key=lambda r: r["net_sales"], reverse=True)

    unmatched_shopify_products = [
        {
            "sku": sku,
            "product_name": shopify_products_by_sku[sku]["product_name"],
            "net_sales": shopify_products_by_sku[sku]["net_sales"],
            "reason": REASON_SHOPIFY_WITHOUT_GA4,
        }
        for sku in sorted(unmatched_shopify_skus)
    ]
    unmatched_ga4_pages = [
        {
            "sku": sku,
            "url": ga4_pages_by_sku[sku]["url"],
            "sessions": ga4_pages_by_sku[sku]["sessions"],
            "reason": REASON_GA4_WITHOUT_SHOPIFY,
        }
        for sku in sorted(unmatched_ga4_skus)
    ]

    mapping_log = {
        "market": market_code,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "matched_count": len(joined),
        "unmatched_shopify_count": len(unmatched_shopify_products),
        "unmatched_ga4_count": len(unmatched_ga4_pages),
        "unmatched_shopify_products": unmatched_shopify_products,
        "unmatched_ga4_pages": unmatched_ga4_pages,
    }

    write_json(join_path(market_code), joined)
    write_json(mapping_log_path(market_code), mapping_log)

    _print_summary(market_code, mapping_log)
    return {"joined": joined, "mapping_log": mapping_log}


def _print_summary(market_code: str, mapping_log: dict) -> None:
    print(f"\n[JOIN {market_code}] {mapping_log['matched_count']} produits rapproches avec succes (SKU <-> page GA4).")
    if mapping_log["unmatched_shopify_count"]:
        print(f"[JOIN {market_code}] {mapping_log['unmatched_shopify_count']} produit(s) Shopify SANS page GA4 - a traiter manuellement :")
        for item in mapping_log["unmatched_shopify_products"]:
            print(f"    - {item['sku']} ({item['product_name']}) - net sales {item['net_sales']}")
    if mapping_log["unmatched_ga4_count"]:
        print(f"[JOIN {market_code}] {mapping_log['unmatched_ga4_count']} page(s) GA4 SANS produit Shopify - a traiter manuellement :")
        for item in mapping_log["unmatched_ga4_pages"]:
            print(f"    - {item['sku']} ({item['url']}) - sessions {item['sessions']}")
    if not mapping_log["unmatched_shopify_count"] and not mapping_log["unmatched_ga4_count"]:
        print(f"[JOIN {market_code}] Aucun echec de mapping.")


def join_all_ecommerce_markets() -> None:
    for market_code in ECOMMERCE_MARKETS:
        join_market(market_code)
