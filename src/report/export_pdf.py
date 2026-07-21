"""
Export PDF du rapport multi-marches HTML via Playwright/Chromium.
Le HTML est autonome (CSS + SVG inline) — aucune ressource reseau.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

from src.utils.io import OUTPUT_DIR

PDF_DIR = OUTPUT_DIR / "pdf"
HTML_PATH = OUTPUT_DIR / "report.html"
PDF_PATH = PDF_DIR / "report.pdf"

_SANDBOX_CHROMIUM = Path("/opt/pw-browsers/chromium")


def _chromium_executable_path() -> str | None:
    return str(_SANDBOX_CHROMIUM) if _SANDBOX_CHROMIUM.exists() else None


def export_pdf() -> Path:
    if not HTML_PATH.exists():
        raise FileNotFoundError(f"{HTML_PATH} introuvable - lancer d'abord `build-report`.")

    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_chromium_executable_path())
        page = browser.new_page()
        page.goto(HTML_PATH.resolve().as_uri())
        page.pdf(
            path=str(PDF_PATH),
            format="A4",
            print_background=True,
            margin={"top": "10mm", "bottom": "10mm", "left": "8mm", "right": "8mm"},
        )
        browser.close()

    print(f"[PDF] écrit -> {PDF_PATH}")
    return PDF_PATH


def export_all_pdfs() -> list[Path]:
    return [export_pdf()]
