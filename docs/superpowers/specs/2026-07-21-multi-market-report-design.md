# Design — Rapport multi-marchés (look type dashboard)

Date : 2026-07-21

## Objectif

Un seul HTML/PDF hebdo (US → UK → INT → FR), rendu proche du screenshot
référence (palette pêche/corail, tuiles KPI, layout compact).

## Contenu par marché

- **US (ecommerce)** : Units, Net Sales, Sessions, Conversion ; courbe
  L6M vs LY ; Top Pages ; Traffic Sources ; Top Products (join Shopify×GA4).
- **UK / INT / FR (traffic)** : Sessions ; Top Pages ; Traffic Sources.
  Pas de Units / Net Sales / Conversion / L6M / Top Products.

Shopify (mock PoC, exports manuels en réel) alimente uniquement l’US.

## Technique

- Template unique `report.html.j2` ; `build-report` → `output/report.html`.
- `export-pdf` → `output/pdf/report.pdf`.
- UK passe en `type: "traffic"` dans `settings.py` (plus de join UK).
- CSS + SVG restylés (palette corail) ; pas de JS externe.
