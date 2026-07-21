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

```bash
python main.py generate-data   # (re)génère les JSON mock GA4/Shopify (US/UK/INT/FR)
python main.py join            # jointure Produit SKU (Shopify x GA4), marchés US/UK
python main.py build-report    # génère les rapports HTML par marché
python main.py export-pdf      # convertit chaque rapport HTML en PDF
python main.py all             # enchaîne les 4 étapes ci-dessus
```

Les rapports HTML sont dans `output/report_<marché>.html` (ouvrables
directement dans un navigateur), les PDF dans `output/pdf/`.

## Structure

- `config/settings.py` — paramètres globaux : marchés, seed, seuil des highlights.
- `src/mock_data/` — catalogue produit + générateurs mock GA4/Shopify.
- `src/join/` — jointure Produit par SKU (Shopify × GA4), avec log des échecs de mapping.
- `src/report/` — highlights (texte auto-généré), graphiques SVG, templates Jinja2, export PDF.
- `data/raw/` — exports mock (équivalent des exports GA4 Data API / Shopify Admin API).
- `data/processed/` — résultat de la jointure + logs de mapping.
- `output/` — rapports HTML et PDF générés.

## Passage au réel

Chaque module mock contient un commentaire `MOCK -> REEL` expliquant
l'appel API à brancher à la place (GA4 Data API `runReport`, Shopify
Admin API GraphQL). Le reste du pipeline (jointure, highlights, rendu)
n'a pas besoin de changer tant que le JSON produit respecte le même schéma.
