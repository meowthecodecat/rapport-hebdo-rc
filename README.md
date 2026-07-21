# rapport-hebdo-rc

Proof of product : génération automatisée d'un rapport hebdomadaire de
performance e-commerce pour une marque de spiritueux premium fictive
("Domaine de Claude"), sur 4 marchés (US, UK, INT, FR).

**Toutes les données sont 100% synthétiques** (mock), générées localement.
Aucun appel API réel, aucune donnée de marque réelle.

## Installation

```bash
pip install -r requirements.txt
```

Playwright a besoin d'un Chromium local pour l'export PDF (déjà présent
dans certains environnements sandbox ; sinon, une seule fois) :

```bash
playwright install chromium
```

## Utilisation

### GA4 (PoC plug-and-play)

Les inputs GA4 de la PoC sont de **faux rapports au format Data API
`runReport`**, versionnés dans `data/fixtures/ga4/<marché>/` :

- `summary.json`
- `top_pages.json`
- `traffic_sources.json`
- `trend_6m.json`

```bash
python main.py generate-ga4-fixtures   # (re)génère les faux runReport
python main.py fetch-ga4               # fixtures -> data/raw/ga4_*.json (schéma canonique)
```

Tu peux éditer les fixtures à la main, ou y coller un vrai dump
`runReport` plus tard : le normalizer (`src/ga4/normalize.py`) produit
toujours le même schéma canonique.

Passage au réel : dans `config/settings.py`, renseigner `GA4_PROPERTY_IDS`,
passer `GA4_MODE = "real"`, et compléter `src/ga4/real_client.py`.

### Pipeline complet (démo)

```bash
python main.py generate-data   # fixtures GA4 + fetch + Shopify mock (US/UK, pour la démo join)
python main.py join            # jointure Produit SKU (Shopify x GA4), marchés US/UK
python main.py build-report    # génère les rapports HTML par marché
python main.py export-pdf      # convertit chaque rapport HTML en PDF
python main.py all             # enchaîne les étapes ci-dessus
```

Les rapports HTML sont dans `output/report_<marché>.html` (ouvrables
directement dans un navigateur), les PDF dans `output/pdf/`.

> **Shopify** : le mock reste uniquement pour démarrer la jointure en
> démo. En usage réel tu fournis tes exports à la main (et tu peux
> ajuster le PDF toi-même) — le focus PoC de ce repo est GA4.

## Structure

- `config/settings.py` — marchés, seed, seuil highlights, `GA4_MODE` / property IDs.
- `data/fixtures/ga4/` — **faux rapports GA4** (format `runReport`), versionnés.
- `src/ga4/` — client mock/réel + normalizer vers le schéma canonique.
- `src/mock_data/` — catalogue produit + générateur Shopify mock (démo join).
- `src/join/` — jointure Produit par SKU (Shopify × GA4), avec log des échecs.
- `src/report/` — highlights, graphiques SVG, templates Jinja2, export PDF.
- `data/raw/` — JSON canoniques générés (`ga4_*.json`, `shopify_*.json`).
- `data/processed/` — résultat de la jointure + logs de mapping.
- `output/` — rapports HTML et PDF générés.

## Passage au réel

- **GA4** : `MockGa4Client` → `RealGa4Client` (`BetaAnalyticsDataClient.run_report`),
  mêmes 4 rapports, même normalizer.
- **Shopify** : remplacer les JSON mock par tes exports manuels / Admin API ;
  la jointure ne change pas tant que le schéma produit (SKU, units, net sales)
  est respecté.
