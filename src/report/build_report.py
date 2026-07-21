"""
Orchestration du rendu HTML : charge les JSON (GA4, Shopify, jointure,
log de mapping) deja generes sur disque, calcule le contexte de
template, et rend un rapport HTML autonome par marche (CSS et SVG
embarques inline - aucune dependance externe, ouverture directe dans un
navigateur ou conversion PDF via Playwright).

MOCK -> REEL : ce module ne change pas. Seule la source des JSON
(data/raw/*.json, aujourd'hui ecrits par les generateurs mock) devrait
un jour venir d'un appel API en direct ; la fonction `build_report`
resterait identique tant que les payloads respectent le meme schema.
"""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config.settings import MARKETS, HIGHLIGHT_THRESHOLD_PCT
from src.mock_data.products_catalog import BRAND_NAME
from src.report.charts import render_traffic_donut, render_trend_chart
from src.report.highlights import generate_highlights
from src.utils.io import (
    OUTPUT_DIR, ga4_path, shopify_path, join_path, mapping_log_path, read_json,
)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
CSS_PATH = TEMPLATES_DIR / "partials" / "style.css"

_CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "EUR": "€"}


def _int_fmt(value: float) -> str:
    return f"{round(value):,}"


def _pct_fmt(value: float) -> str:
    return f"{value:+.1f}%"


def _money_fmt(value: float, currency: str) -> str:
    symbol = _CURRENCY_SYMBOLS.get(currency, "")
    return f"{symbol}{value:,.0f}"


def _make_env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    env.filters["int_fmt"] = _int_fmt
    env.filters["pct_fmt"] = _pct_fmt
    env.filters["money_fmt"] = _money_fmt
    return env


def _base_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def build_report(market_code: str) -> Path:
    cfg = MARKETS[market_code]
    ga4 = read_json(ga4_path(market_code))
    env = _make_env()

    common = {
        "market_code": market_code,
        "market_name": cfg["name"],
        "brand_name": BRAND_NAME,
        "period": ga4["period"],
        "base_css": _base_css(),
        "top_pages": ga4["top_pages"],
        "traffic_donut_svg": render_traffic_donut(ga4["traffic_sources"]),
        "traffic_sources": ga4["traffic_sources"],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    if cfg["type"] == "ecommerce":
        shopify = read_json(shopify_path(market_code))
        top_products = read_json(join_path(market_code))
        mapping_log = read_json(mapping_log_path(market_code))

        scorecards = [
            {
                "label": "Units", "kind": "int",
                "value": shopify["summary"]["units"],
                "vs_lw": shopify["summary"]["units_vs_lw_pct"],
                "vs_ly": shopify["summary"]["units_vs_ly_pct"],
            },
            {
                "label": "Net Sales", "kind": "money",
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
                "label": "Conversion Rate", "kind": "rate",
                "value": ga4["summary"]["conversion_rate"],
                "vs_lw": ga4["summary"]["conversion_rate_vs_lw_pct"],
                "vs_ly": ga4["summary"]["conversion_rate_vs_ly_pct"],
            },
        ]

        context = {
            **common,
            "currency": cfg["currency"],
            "scorecards": scorecards,
            "trend_chart_svg": render_trend_chart(ga4["trend_6m"]),
            "top_products": top_products[:10],
            "mapping_log": mapping_log,
        }
        template = env.get_template("report_ecommerce.html.j2")
    else:
        highlights = generate_highlights(ga4, shopify=None, threshold_pct=HIGHLIGHT_THRESHOLD_PCT)
        context = {
            **common,
            "sessions_card": {
                "value": ga4["summary"]["sessions"],
                "vs_lw": ga4["summary"]["sessions_vs_lw_pct"],
                "vs_ly": ga4["summary"]["sessions_vs_ly_pct"],
            },
            "highlights": highlights,
            "highlight_threshold_pct": HIGHLIGHT_THRESHOLD_PCT,
        }
        template = env.get_template("report_traffic.html.j2")

    html = template.render(**context)
    out_path = OUTPUT_DIR / f"report_{market_code.lower()}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"[REPORT {market_code}] écrit -> {out_path}")
    return out_path


def build_all_reports() -> list[Path]:
    return [build_report(market_code) for market_code in MARKETS]
