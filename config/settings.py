"""
Parametres globaux du proof of product.

Tout ce qui est specifique a un marche (volumetrie, mix de canaux,
devise, type de rapport) est centralise ici, pour que la logique de
generation / jointure / reporting reste generique et ne "connaisse" pas
les marches en dur.

MOCK -> REEL : RNG_SEED et les volumes de base disparaissent. Le reste
(HIGHLIGHT_THRESHOLD_PCT, MARKETS[*]['type'], le mapping des canaux)
reste utile tel quel pour piloter le vrai pipeline GA4/Shopify.
"""

# Graine du generateur pseudo-aleatoire : memes donnees mock a chaque
# execution (reproductibilite pour les demos / tests).
RNG_SEED = 42

# ---------------------------------------------------------------------------
# GA4 PoC plug-and-play
# ---------------------------------------------------------------------------
# "mock" -> lit data/fixtures/ga4/<market>/*.json (faux runReport)
# "real" -> src/ga4/real_client.py (a brancher sur BetaAnalyticsDataClient)
GA4_MODE = "mock"

# Remplacer REPLACE_* par les vrais property IDs le jour du branchement API.
# Format attendu par la Data API : "properties/123456789"
GA4_PROPERTY_IDS = {
    "US": "properties/REPLACE_US",
    "UK": "properties/REPLACE_UK",
    "INT": "properties/REPLACE_INT",
    "FR": "properties/REPLACE_FR",
}

# Seuil (en %) au-dela duquel un ecart vs LW ou vs LY declenche un
# highlight dans le rapport. Modifiable sans toucher au code.
HIGHLIGHT_THRESHOLD_PCT = 15

# Les 10 canaux GA4 attendus, dans l'ordre d'affichage par defaut du
# pie chart (avant tri par volume). La couleur de chaque canal dans le
# rapport est fixee sur ce nom, jamais sur son rang -> l'identite visuelle
# d'un canal ne change pas d'un marche/d'une semaine a l'autre.
TRAFFIC_CHANNELS = [
    "Organic Search",
    "Paid Social",
    "Direct",
    "Unassigned",
    "Organic Social",
    "Referral",
    "Display",
    "Email",
    "Paid Search",
    "Cross-network",
]

# type: "ecommerce" -> scorecards Units/Net Sales/Sessions/Conversion,
#       courbe L6M, top pages, pie traffic sources, top products (join).
#       Réservé à l'US dans le rapport multi-marchés.
#       "traffic"   -> KPI Sessions, top pages, pie traffic sources
#       (UK / INT / FR — pas de données Shopify dans le rapport).
MARKETS = {
    "US": {
        "name": "United States",
        "type": "ecommerce",
        "currency": "USD",
        "base_sessions": 52000,
        "base_conversion_rate": 1.62,
        "seed_offset": 1,
        "traffic_mix": {
            "Organic Search": 0.24, "Paid Social": 0.18, "Direct": 0.14,
            "Paid Search": 0.13, "Organic Social": 0.09, "Email": 0.08,
            "Referral": 0.06, "Display": 0.04, "Unassigned": 0.03, "Cross-network": 0.01,
        },
    },
    "UK": {
        "name": "United Kingdom",
        "type": "traffic",
        "currency": "GBP",
        "base_sessions": 21000,
        "base_conversion_rate": 1.45,
        "seed_offset": 2,
        "traffic_mix": {
            "Organic Search": 0.27, "Direct": 0.16, "Paid Social": 0.14,
            "Email": 0.11, "Paid Search": 0.10, "Organic Social": 0.08,
            "Referral": 0.06, "Display": 0.04, "Unassigned": 0.03, "Cross-network": 0.01,
        },
    },
    "INT": {
        "name": "International (Rest of World)",
        "type": "traffic",
        "currency": "USD",
        "base_sessions": 12500,
        "base_conversion_rate": 0.90,
        "seed_offset": 3,
        "traffic_mix": {
            "Organic Search": 0.32, "Referral": 0.15, "Direct": 0.14,
            "Organic Social": 0.12, "Paid Social": 0.10, "Unassigned": 0.06,
            "Paid Search": 0.05, "Email": 0.03, "Display": 0.02, "Cross-network": 0.01,
        },
    },
    "FR": {
        "name": "France",
        "type": "traffic",
        "currency": "EUR",
        "base_sessions": 8200,
        "base_conversion_rate": 1.10,
        "seed_offset": 4,
        "traffic_mix": {
            "Organic Search": 0.29, "Direct": 0.18, "Organic Social": 0.14,
            "Email": 0.10, "Referral": 0.09, "Paid Social": 0.08,
            "Paid Search": 0.06, "Unassigned": 0.03, "Display": 0.02, "Cross-network": 0.01,
        },
    },
}

ECOMMERCE_MARKETS = [m for m, cfg in MARKETS.items() if cfg["type"] == "ecommerce"]
TRAFFIC_MARKETS = [m for m, cfg in MARKETS.items() if cfg["type"] == "traffic"]
ALL_MARKETS = list(MARKETS.keys())
