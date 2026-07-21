"""
Catalogue produit partage entre les generateurs GA4 et Shopify.

Le champ `slug` est ce qui garantit la coherence entre l'URL de la page
produit GA4 (/products/<slug>) et le SKU Shopify : c'est exactement la
cle de jointure utilisee par src/join/join_product_performance.py.

Marque fictive : "Domaine de Claude" - aucune donnee, nom ou visuel reel
de marque existante n'est utilise nulle part dans ce projet.

MOCK -> REEL : ce fichier disparait en prod. Le catalogue viendrait de
Shopify (GET /products.json ou GraphQL `products`) et le rapprochement
avec les pages GA4 se ferait sur le path de la page (dimension
`pagePath`) en extrayant le slug, exactement comme fait ici.
"""

from dataclasses import dataclass

BRAND_NAME = "Domaine de Claude"


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    category: str
    price: float  # prix TTC unitaire, dans la devise du marche (converti par marche si besoin)
    slug: str  # -> URL GA4 : /products/<slug>


PRODUCTS: list[Product] = [
    Product("COG-XO-700", f"{BRAND_NAME} XO Cognac 70cl", "Cognac", 89.00, "xo-cognac-70cl"),
    Product("COG-VSOP-700", f"{BRAND_NAME} VSOP Cognac 70cl", "Cognac", 54.00, "vsop-cognac-70cl"),
    Product("COG-VS-700", f"{BRAND_NAME} VS Cognac 70cl", "Cognac", 38.00, "vs-cognac-70cl"),
    Product("GIN-LDN-700", f"{BRAND_NAME} London Dry Gin 70cl", "Gin", 42.00, "london-dry-gin-70cl"),
    Product("GIN-BAR-700", f"{BRAND_NAME} Barrel-Aged Gin 70cl", "Gin", 48.00, "barrel-aged-gin-70cl"),
    Product("VOD-ORG-700", f"{BRAND_NAME} Original Vodka 70cl", "Vodka", 36.00, "original-vodka-70cl"),
    Product("VOD-CIT-700", f"{BRAND_NAME} Citrus Vodka 70cl", "Vodka", 38.00, "citrus-vodka-70cl"),
    Product("WHY-SGL-700", f"{BRAND_NAME} Single Malt Whisky 70cl", "Whisky", 65.00, "single-malt-whisky-70cl"),
    Product("WHY-BLD-700", f"{BRAND_NAME} Blended Whisky 70cl", "Whisky", 45.00, "blended-whisky-70cl"),
    Product("LIQ-ORG-500", f"{BRAND_NAME} Orange Liqueur 50cl", "Liqueur", 32.00, "orange-liqueur-50cl"),
    Product("LIQ-HRB-500", f"{BRAND_NAME} Herbal Liqueur 50cl", "Liqueur", 34.00, "herbal-liqueur-50cl"),
    Product("GFT-DISC-000", f"{BRAND_NAME} Discovery Gift Set", "Gift Set", 120.00, "discovery-gift-set"),
    Product("LTD-ANNIV-700", f"{BRAND_NAME} Anniversary Limited Edition 70cl", "Limited Edition", 145.00, "anniversary-limited-edition-70cl"),
]

# Injecte volontairement pour la demo du mapping :
# - GFT-DISC-000 (au-dessus) existe cote Shopify mais n'aura PAS de page
#   GA4 generee (vendu en tunnel bundle, jamais visite comme PDP autonome)
#   -> cas "produit Shopify sans page GA4".
NO_GA4_PAGE_SKUS = {"GFT-DISC-000"}

# - Une page GA4 "orpheline" (slug produit discontinue) qui n'a pas de
#   SKU Shopify correspondant -> cas "page GA4 sans produit Shopify".
ORPHAN_GA4_PAGE = {
    "url": "/products/vintage-reserve-cognac-40cl-2019",
    "sku": "COG-VTG-2019-DISC",
    "name": f"{BRAND_NAME} Vintage Reserve Cognac 40cl (2019, discontinued)",
}


def products_for_ga4() -> list[Product]:
    """Produits eligibles a une page produit (PDP) trackee en GA4."""
    return [p for p in PRODUCTS if p.sku not in NO_GA4_PAGE_SKUS]


def products_for_shopify() -> list[Product]:
    """Tous les produits vendables cote Shopify (catalogue complet)."""
    return list(PRODUCTS)
