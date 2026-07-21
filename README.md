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

Playwright a besoin d'un Chromium local pour l'export PDF :

```bash
python -m playwright install chromium
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

Passage au réel : dans `config/settings.py`, renseigner `GA4_PROPERTY_IDS`,
passer `GA4_MODE = "real"`, et compléter `src/ga4/real_client.py`.

### Pipeline complet (démo)

```bash
python main.py generate-data   # fixtures GA4 + fetch + Shopify mock (US, pour la démo join)
python main.py join            # jointure Produit SKU (Shopify x GA4), US uniquement
python main.py build-report    # génère output/report.html (multi-marchés)
python main.py export-pdf      # convertit en output/pdf/report.pdf
python main.py all             # enchaîne les étapes ci-dessus
```

### Contenu du rapport

Un seul document empilé **US → UK → INT → FR** :

| Bloc | US | UK / INT / FR |
|------|----|---------------|
| Units, Net Sales, Conversion | oui | non |
| Sessions | oui | oui |
| Courbe L6M vs LY | oui | non |
| Top Pages | oui | oui |
| Traffic Sources | oui | oui |
| Top Products | oui | non |

Shopify (mock PoC ; en réel : tes exports) alimente **uniquement l’US**
(Units, Net Sales, Top Products).

> **Shopify** : le mock reste pour démarrer la jointure en démo. En usage
> réel tu fournis tes exports à la main — le focus PoC de ce repo est GA4.

## Structure

- `config/settings.py` — marchés, seed, `GA4_MODE` / property IDs.
- `data/fixtures/ga4/` — **faux rapports GA4** (format `runReport`), versionnés.
- `src/ga4/` — client mock/réel + normalizer vers le schéma canonique.
- `src/mock_data/` — catalogue produit + générateur Shopify mock (démo join US).
- `src/join/` — jointure Produit par SKU (Shopify × GA4), avec log des échecs.
- `src/report/` — templates Jinja2, graphiques SVG, export PDF.
- `data/raw/` — JSON canoniques générés (`ga4_*.json`, `shopify_us.json`).
- `data/processed/` — résultat de la jointure + logs de mapping.
- `output/report.html` / `output/pdf/report.pdf` — rapport multi-marchés.

## Passage au réel

- **GA4** : `MockGa4Client` → `RealGa4Client` (`BetaAnalyticsDataClient.run_report`),
  mêmes 4 rapports, même normalizer.
- **Shopify** : remplacer le JSON mock US par ton export manuel / Admin API ;
  la jointure ne change pas tant que le schéma produit (SKU, units, net sales)
  est respecté.
