"""
Generateur de donnees mock "façon export Shopify Admin API" pour un marche
e-commerce (US/UK). Les marches trafic (INT/FR) n'ont pas de canal de
vente e-commerce local dans ce POC : ils ne recoivent donc pas de
dataset Shopify (voir config.settings.MARKETS[*]['type']).

Le volume par produit est deduit du trafic GA4 de la page produit
correspondante (dataset GA4 deja genere pour le meme marche), pour que
le join units/net_sales <-> sessions/conversion produise des taux de
conversion par produit plausibles plutot que deux series independantes.

MOCK -> REEL : remplacer `generate_shopify_dataset()` par des appels a
la Shopify Admin API (GraphQL `orders` + `productVariants`, filtres sur
`created_at` pour chaque plage de dates), agreges par SKU. La forme du
JSON (summary + products[]) resterait identique pour ne rien casser en
aval (jointure, rapport).
"""

import random
from datetime import date

from config.settings import MARKETS, RNG_SEED
from src.mock_data.products_catalog import products_for_shopify
from src.mock_data.rng_helpers import pct, delta_with_occasional_outlier
from src.utils.dates import build_period


def _sessions_by_sku(ga4_dataset: dict) -> dict[str, int]:
    return {
        page["sku"]: page["sessions"]
        for page in ga4_dataset["top_pages"]
        if page["sku"] is not None
    }


def scaffold_shopify_template(market_code: str, today: date | None = None) -> dict:
    """Gabarit vide (mêmes clés que le dataset mock, valeurs à 0) destiné
    à être rempli à la main avec de vraies données Shopify, le temps de
    ne pas encore brancher l'Admin API. Un produit = une ligne à remplir ;
    le SKU ne doit pas être modifié (c'est la clé de jointure avec GA4).

    `summary` n'est PAS recalculé automatiquement à partir de `products` :
    remplissez les deux, `summary` porte les totaux + variations globales,
    `products` le détail par SKU utilisé par la table Top Products.
    """
    cfg = MARKETS[market_code]
    if cfg["type"] != "ecommerce":
        raise ValueError(f"{market_code} n'est pas un marche e-commerce : pas de gabarit Shopify a creer.")

    return {
        "market": market_code,
        "currency": cfg["currency"],
        "period": build_period(today),
        "summary": {
            "orders": 0,
            "units": 0,
            "net_sales": 0.0,
            "orders_vs_lw_pct": 0.0,
            "units_vs_lw_pct": 0.0,
            "net_sales_vs_lw_pct": 0.0,
            "orders_vs_ly_pct": 0.0,
            "units_vs_ly_pct": 0.0,
            "net_sales_vs_ly_pct": 0.0,
        },
        "products": [
            {
                "sku": product.sku,
                "product_name": product.name,
                "category": product.category,
                "orders": 0,
                "units": 0,
                "net_sales": 0.0,
                "units_vs_lw_pct": 0.0,
                "net_sales_vs_lw_pct": 0.0,
            }
            for product in products_for_shopify()
        ],
    }


def generate_shopify_dataset(market_code: str, ga4_dataset: dict, today: date | None = None) -> dict:
    cfg = MARKETS[market_code]
    if cfg["type"] != "ecommerce":
        raise ValueError(f"{market_code} n'est pas un marche e-commerce : pas de dataset Shopify a generer.")

    rng = random.Random(RNG_SEED + cfg["seed_offset"] * 2000)
    sessions_by_sku = _sessions_by_sku(ga4_dataset)

    products = []
    for product in products_for_shopify():
        pdp_sessions = sessions_by_sku.get(product.sku)
        if pdp_sessions is not None:
            conversion_rate = rng.uniform(1.0, 3.2)  # %
            orders = max(round(pdp_sessions * conversion_rate / 100), 1)
        else:
            # Produit sans page PDP trackee (ex: gift set vendu en tunnel
            # bundle) : volume estime independamment du trafic GA4.
            orders = rng.randint(12, 35)

        units = max(round(orders * rng.uniform(1.0, 1.3)), orders)
        net_sales = round(units * product.price * rng.uniform(0.92, 1.05), 2)

        products.append({
            "sku": product.sku,
            "product_name": product.name,
            "category": product.category,
            "orders": orders,
            "units": units,
            "net_sales": net_sales,
            "units_vs_lw_pct": delta_with_occasional_outlier(rng),
            "net_sales_vs_lw_pct": delta_with_occasional_outlier(rng),
        })

    products.sort(key=lambda p: p["net_sales"], reverse=True)

    total_orders = sum(p["orders"] for p in products)
    total_units = sum(p["units"] for p in products)
    total_net_sales = round(sum(p["net_sales"] for p in products), 2)

    return {
        "market": market_code,
        "currency": cfg["currency"],
        "period": build_period(today),
        "summary": {
            "orders": total_orders,
            "units": total_units,
            "net_sales": total_net_sales,
            "orders_vs_lw_pct": pct(rng, -8, 14),
            "units_vs_lw_pct": pct(rng, -8, 14),
            "net_sales_vs_lw_pct": pct(rng, -8, 16),
            "orders_vs_ly_pct": pct(rng, -12, 12),
            "units_vs_ly_pct": pct(rng, -12, 12),
            "net_sales_vs_ly_pct": pct(rng, -12, 14),
        },
        "products": products,
    }
