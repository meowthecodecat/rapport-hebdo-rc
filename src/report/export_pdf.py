"""
Export PDF des rapports HTML, via Playwright/Chromium headless (deja
installes dans l'environnement d'execution - aucun telechargement de
navigateur necessaire). Chaque rapport est deja un fichier HTML
autonome (CSS + SVG inline), donc l'impression PDF ne depend d'aucune
ressource reseau.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

from config.settings import ALL_MARKETS
from src.utils.io import OUTPUT_DIR

PDF_DIR = OUTPUT_DIR / "pdf"

# Certains environnements sandbox pre-installent Chromium a un chemin fixe
# (hors du cache Playwright standard). S'il existe, on l'utilise ; sinon on
# laisse Playwright resoudre son propre navigateur (cas normal en local,
# apres un `playwright install`).
_SANDBOX_CHROMIUM = Path("/opt/pw-browsers/chromium")


def _chromium_executable_path() -> str | None:
    return str(_SANDBOX_CHROMIUM) if _SANDBOX_CHROMIUM.exists() else None


def export_pdf(market_code: str) -> Path:
    html_path = OUTPUT_DIR / f"report_{market_code.lower()}.html"
    if not html_path.exists():
        raise FileNotFoundError(f"{html_path} introuvable - lancer d'abord `build-report`.")

    pdf_path = PDF_DIR / f"report_{market_code.lower()}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_chromium_executable_path())
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri())
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "12mm", "bottom": "12mm", "left": "8mm", "right": "8mm"},
        )
        browser.close()

    print(f"[PDF {market_code}] écrit -> {pdf_path}")
    return pdf_path


def export_all_pdfs() -> list[Path]:
    return [export_pdf(market_code) for market_code in ALL_MARKETS]
