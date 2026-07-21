"""
Point d'entree unique du pipeline (proof of product, données 100%
synthétiques - marque fictive "Domaine de Claude").

Usage :
    python main.py generate-data   # (re)génère les JSON mock GA4/Shopify (US/UK/INT/FR)
    python main.py join            # jointure Produit SKU (Shopify x GA4), marchés US/UK
    python main.py build-report    # génère les rapports HTML par marché (data/ -> output/)
    python main.py export-pdf      # convertit chaque rapport HTML en PDF (via Playwright)
    python main.py all             # enchaîne les 4 étapes ci-dessus
"""

import argparse

from config.settings import ALL_MARKETS, ECOMMERCE_MARKETS
from src.join.join_product_performance import join_all_ecommerce_markets
from src.mock_data.generate_ga4 import generate_ga4_dataset
from src.mock_data.generate_shopify import generate_shopify_dataset
from src.report.build_report import build_all_reports
from src.report.export_pdf import export_all_pdfs
from src.utils.io import ga4_path, shopify_path, write_json


def cmd_generate_data() -> None:
    ga4_by_market = {}
    for market_code in ALL_MARKETS:
        ga4 = generate_ga4_dataset(market_code)
        ga4_by_market[market_code] = ga4
        write_json(ga4_path(market_code), ga4)
        print(f"[GENERATE {market_code}] GA4 -> {ga4_path(market_code)}")

    for market_code in ECOMMERCE_MARKETS:
        shopify = generate_shopify_dataset(market_code, ga4_by_market[market_code])
        write_json(shopify_path(market_code), shopify)
        print(f"[GENERATE {market_code}] Shopify -> {shopify_path(market_code)}")


def cmd_join() -> None:
    join_all_ecommerce_markets()


def cmd_build_report() -> None:
    build_all_reports()


def cmd_export_pdf() -> None:
    export_all_pdfs()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate-data", help="Génère les datasets mock GA4/Shopify (US/UK/INT/FR).")
    sub.add_parser("join", help="Jointure Produit SKU (Shopify x GA4) pour US/UK.")
    sub.add_parser("build-report", help="Génère les rapports HTML par marché.")
    sub.add_parser("export-pdf", help="Exporte chaque rapport HTML en PDF (Playwright).")
    sub.add_parser("all", help="Enchaîne generate-data -> join -> build-report -> export-pdf.")

    args = parser.parse_args()
    commands = {
        "generate-data": [cmd_generate_data],
        "join": [cmd_join],
        "build-report": [cmd_build_report],
        "export-pdf": [cmd_export_pdf],
        "all": [cmd_generate_data, cmd_join, cmd_build_report, cmd_export_pdf],
    }
    for step in commands[args.command]:
        step()


if __name__ == "__main__":
    main()
