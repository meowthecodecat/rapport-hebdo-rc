"""
Point d'entree unique du pipeline (proof of product, données 100%
synthétiques - marque fictive "Domaine de Claude").

Usage :
    python main.py generate-ga4-fixtures  # (re)génère les faux rapports GA4 Data API
    python main.py fetch-ga4              # fixtures/API -> data/raw/ga4_*.json (canonique)
    python main.py generate-data          # fetch-ga4 + mock Shopify (US) pour la démo join
    python main.py join                   # jointure Produit SKU (Shopify x GA4), US uniquement
    python main.py build-report           # génère le rapport HTML multi-marchés
    python main.py export-pdf             # convertit le rapport HTML en PDF
    python main.py all                    # enchaîne fixtures -> fetch-ga4 -> shopify -> join -> report -> pdf

Rapport : un seul document US -> UK -> INT -> FR.
US = e-commerce (Units/Sales/Sessions/Conversion, L6M, top pages, sources, top products).
UK/INT/FR = trafic (Sessions, top pages, sources).
"""

import argparse

from config.settings import ALL_MARKETS, ECOMMERCE_MARKETS
from src.ga4.client import fetch_canonical_ga4
from src.ga4.fixture_generator import generate_all_fixtures
from src.join.join_product_performance import join_all_ecommerce_markets
from src.mock_data.generate_shopify import generate_shopify_dataset
from src.report.build_report import build_all_reports
from src.report.export_pdf import export_all_pdfs
from src.utils.io import ga4_path, read_json, shopify_path, write_json


def cmd_generate_ga4_fixtures() -> None:
    written = generate_all_fixtures()
    for market, paths in written.items():
        print(f"[GA4 FIXTURES {market}]")
        for path in paths:
            print(f"  -> {path}")


def cmd_fetch_ga4() -> None:
    for market_code in ALL_MARKETS:
        ga4 = fetch_canonical_ga4(market_code)
        write_json(ga4_path(market_code), ga4)
        print(f"[FETCH GA4 {market_code}] -> {ga4_path(market_code)}")


def cmd_generate_shopify_mock() -> None:
    """Shopify mock uniquement pour alimenter la démo de jointure US."""
    for market_code in ECOMMERCE_MARKETS:
        ga4 = read_json(ga4_path(market_code))
        shopify = generate_shopify_dataset(market_code, ga4)
        write_json(shopify_path(market_code), shopify)
        print(f"[GENERATE {market_code}] Shopify mock -> {shopify_path(market_code)}")


def cmd_generate_data() -> None:
    """Raccourci démo : fixtures GA4 -> canonique + Shopify mock."""
    cmd_generate_ga4_fixtures()
    cmd_fetch_ga4()
    cmd_generate_shopify_mock()


def cmd_join() -> None:
    join_all_ecommerce_markets()


def cmd_build_report() -> None:
    build_all_reports()


def cmd_export_pdf() -> None:
    export_all_pdfs()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "generate-ga4-fixtures",
        help="Génère les faux rapports GA4 (format Data API runReport) dans data/fixtures/ga4/.",
    )
    sub.add_parser(
        "fetch-ga4",
        help="Lit fixtures (ou API si GA4_MODE=real) et écrit data/raw/ga4_*.json canonique.",
    )
    sub.add_parser("join", help="Jointure Produit SKU (Shopify x GA4) pour l'US.")
    sub.add_parser("build-report", help="Génère le rapport HTML multi-marchés.")
    sub.add_parser("export-pdf", help="Exporte le rapport HTML en PDF (Playwright).")
    sub.add_parser(
        "generate-data",
        help="Démo complète amont : fixtures GA4 + fetch + Shopify mock (US).",
    )
    sub.add_parser(
        "all",
        help="Enchaîne generate-data -> join -> build-report -> export-pdf.",
    )

    args = parser.parse_args()
    commands = {
        "generate-ga4-fixtures": [cmd_generate_ga4_fixtures],
        "fetch-ga4": [cmd_fetch_ga4],
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
