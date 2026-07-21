"""
Couche GA4 plug-and-play.

PoC : on lit de faux rapports au format GA4 Data API (`runReport`) depuis
`data/fixtures/ga4/`, puis on les normalise vers le schema canonique
consomme par join / highlights / rapports.

Passage au reel : basculer `GA4_MODE = "real"` dans config/settings.py et
implementer les appels dans `src/ga4/real_client.py` (meme signature que
le mock). Le normalizer et le reste du pipeline ne changent pas.
"""

from src.ga4.client import fetch_canonical_ga4

__all__ = ["fetch_canonical_ga4"]
