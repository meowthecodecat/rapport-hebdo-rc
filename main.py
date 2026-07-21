"""
Point d'entree unique du pipeline (proof of product, données 100%
synthétiques - marque fictive "Domaine de Claude").

Usage :
    python main.py generate-data          # (re)génère les JSON mock GA4 (US/UK/INT/FR)
    python main.py scaffold-shopify       # crée un gabarit Shopify vide à remplir à la main (US/UK)
    python main.py generate-mock-shopify  # (re)génère des données Shopify mock aléatoires (démo)
    python main.py join                   # jointure Produit SKU (Shopify x GA4), marchés US/UK
    python main.py build-report           # génère les rapports HTML par marché (data/ -> output/)
    python main.py export-pdf             # convertit chaque rapport HTML en PDF (via Playwright)
    python main.py all                    # enchaîne generate-data -> join -> build-report -> export-pdf

Note sur Shopify : `generate-data` ne touche plus aux fichiers
data/raw/shopify_<marché>.json. Cela permet de les remplir à la main
(cf. `scaffold-shopify`) sans qu'un `python main.py all` ultérieur
n'écrase vos saisies. `generate-mock-shopify` reste disponible pour
revenir à des données 100% mock si besoin (il écrase le fichier).
"""

import argparse

from config.settings import ALL_MARKETS, ECOMMERCE_MARKETS
from src.join.join_product_performance import join_all_ecommerce_markets
from src.mock_data.generate_ga4 import generate_ga4_dataset
from src.mock_data.generate_shopify import generate_shopify_dataset, scaffold_shopify_template
from src.report.build_report import build_all_reports
from src.report.export_pdf import export_all_pdfs
from src.utils.io import ga4_path, shopify_path, read_json, write_json


def cmd_generate_data() -> None:
    for market_code in ALL_MARKETS:
        ga4 = generate_ga4_dataset(market_code)
        write_json(ga4_path(market_code), ga4)
        print(f"[GENERATE {market_code}] GA4 -> {ga4_path(market_code)}")


def cmd_scaffold_shopify() -> None:
    for market_code in ECOMMERCE_MARKETS:
        path = shopify_path(market_code)
        if path.exists():
            print(f"[SCAFFOLD {market_code}] {path} existe déjà - non modifié (pour ne pas écraser une saisie manuelle).")
            continue
        write_json(path, scaffold_shopify_template(market_code))
        print(f"[SCAFFOLD {market_code}] Gabarit vide créé -> {path} (à remplir à la main)")


def cmd_generate_mock_shopify() -> None:
    for market_code in ECOMMERCE_MARKETS:
        ga4 = read_json(ga4_path(market_code))
        shopify = generate_shopify_dataset(market_code, ga4)
        write_json(shopify_path(market_code), shopify)
        print(f"[MOCK {market_code}] Shopify -> {shopify_path(market_code)}")


def cmd_join() -> None:
    join_all_ecommerce_markets()


def cmd_build_report() -> None:
    build_all_reports()


def cmd_export_pdf() -> None:
    export_all_pdfs()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate-data", help="Génère les datasets mock GA4 (US/UK/INT/FR).")
    sub.add_parser("scaffold-shopify", help="Crée un gabarit Shopify vide à remplir à la main (US/UK), sans écraser un fichier existant.")
    sub.add_parser("generate-mock-shopify", help="(Re)génère des données Shopify mock aléatoires (démo, écrase le fichier).")
    sub.add_parser("join", help="Jointure Produit SKU (Shopify x GA4) pour US/UK.")
    sub.add_parser("build-report", help="Génère les rapports HTML par marché.")
    sub.add_parser("export-pdf", help="Exporte chaque rapport HTML en PDF (Playwright).")
    sub.add_parser("all", help="Enchaîne generate-data -> join -> build-report -> export-pdf.")

    args = parser.parse_args()
    commands = {
        "generate-data": [cmd_generate_data],
        "scaffold-shopify": [cmd_scaffold_shopify],
        "generate-mock-shopify": [cmd_generate_mock_shopify],
        "join": [cmd_join],
        "build-report": [cmd_build_report],
        "export-pdf": [cmd_export_pdf],
        "all": [cmd_generate_data, cmd_join, cmd_build_report, cmd_export_pdf],
    }
    for step in commands[args.command]:
        step()


if __name__ == "__main__":
    main()
