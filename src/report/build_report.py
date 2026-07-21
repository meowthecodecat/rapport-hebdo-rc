"""
Orchestration du rendu HTML multi-marches : un seul rapport
(output/report.html) empilant US -> UK -> INT -> FR.

- US (ecommerce) : Units / Net Sales / Sessions / Conversion, courbe L6M,
  top pages, traffic sources, top products (join Shopify x GA4).
- UK / INT / FR (traffic) : Sessions, top pages, traffic sources.

CSS et SVG embarques inline (HTML autonome, export PDF Playwright).
"""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config.settings import MARKETS
from src.mock_data.products_catalog import BRAND_NAME
from src.report.charts import render_traffic_donut, render_trend_chart
from src.utils.io import (
    OUTPUT_DIR, ga4_path, shopify_path, join_path, read_json,
)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
CSS_PATH = TEMPLATES_DIR / "partials" / "style.css"
REPORT_PATH = OUTPUT_DIR / "report.html"

_CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "EUR": "€"}


def _int_fmt(value: float) -> str:
    return f"{round(value):,}"


def _pct_fmt(value: float) -> str:
    return f"{value:+.0f}%"


def _money_fmt(value: float, currency: str) -> str:
    symbol = _CURRENCY_SYMBOLS.get(currency, "")
    return f"{symbol}{value:,.2f}"


def _make_env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    env.filters["int_fmt"] = _int_fmt
    env.filters["pct_fmt"] = _pct_fmt
    env.filters["money_fmt"] = _money_fmt
    return env


def _base_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def _market_context(market_code: str) -> dict:
    cfg = MARKETS[market_code]
    ga4 = read_json(ga4_path(market_code))

    block = {
        "market_code": market_code,
        "market_name": cfg["name"],
        "type": cfg["type"],
        "currency": cfg["currency"],
        "top_pages": ga4["top_pages"][:8],
        "traffic_donut_svg": render_traffic_donut(ga4["traffic_sources"], width=280, height=240),
    }

    if cfg["type"] == "ecommerce":
        shopify = read_json(shopify_path(market_code))
        top_products = read_json(join_path(market_code))
        block.update({
            "scorecards": [
                {
                    "label": "Units", "kind": "int",
                    "value": shopify["summary"]["units"],
                    "vs_lw": shopify["summary"]["units_vs_lw_pct"],
                    "vs_ly": shopify["summary"]["units_vs_ly_pct"],
                },
                {
                    "label": "Sales", "kind": "money",
                    "value": shopify["summary"]["net_sales"],
                    "vs_lw": shopify["summary"]["net_sales_vs_lw_pct"],
                    "vs_ly": shopify["summary"]["net_sales_vs_ly_pct"],
                },
                {
                    "label": "Sessions", "kind": "int",
                    "value": ga4["summary"]["sessions"],
                    "vs_lw": ga4["summary"]["sessions_vs_lw_pct"],
                    "vs_ly": ga4["summary"]["sessions_vs_ly_pct"],
                },
                {
                    "label": "Conversion", "kind": "rate",
                    "value": ga4["summary"]["conversion_rate"],
                    "vs_lw": ga4["summary"]["conversion_rate_vs_lw_pct"],
                    "vs_ly": ga4["summary"]["conversion_rate_vs_ly_pct"],
                },
            ],
            "trend_chart_svg": render_trend_chart(ga4["trend_6m"], width=900, height=240),
            "top_products": top_products[:10],
        })
    else:
        block["sessions_card"] = {
            "value": ga4["summary"]["sessions"],
            "vs_lw": ga4["summary"]["sessions_vs_lw_pct"],
            "vs_ly": ga4["summary"]["sessions_vs_ly_pct"],
        }

    return block


def build_report() -> Path:
    """Genere le rapport multi-marches unique."""
    env = _make_env()
    markets = [_market_context(code) for code in MARKETS]
    # Periode prise sur le premier marche (meme semaine pour tous en PoC).
    first_ga4 = read_json(ga4_path(next(iter(MARKETS))))

    context = {
        "brand_name": BRAND_NAME,
        "period": first_ga4["period"],
        "base_css": _base_css(),
        "markets": markets,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    html = env.get_template("report.html.j2").render(**context)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(html, encoding="utf-8")
    print(f"[REPORT] écrit -> {REPORT_PATH}")
    return REPORT_PATH


def build_all_reports() -> list[Path]:
    """Compat pipeline : un seul fichier multi-marches."""
    return [build_report()]
