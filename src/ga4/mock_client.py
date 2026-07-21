"""
Client mock : lit les faux rapports GA4 (JSON au format runReport)
depuis data/fixtures/ga4/<market>/.

Aucun reseau. Ideal pour la PoC et les demos offline.
"""

from __future__ import annotations

from src.ga4.paths import REPORT_NAMES, fixture_path
from src.utils.io import read_json


class MockGa4Client:
    """Equivalent local d'un BetaAnalyticsDataClient.run_report."""

    def fetch_reports(self, market_code: str, period: dict) -> dict[str, dict]:
        """
        Retourne un dict {report_name: payload_runReport}.

        `period` est ignore cote mock (les dates sont deja dans les fixtures)
        mais conserve dans la signature pour rester iso avec RealGa4Client.
        """
        _ = period  # volontairement inutilise en mock
        bundle: dict[str, dict] = {}
        missing: list[str] = []
        for name in REPORT_NAMES:
            path = fixture_path(market_code, name)
            if not path.exists():
                missing.append(str(path))
                continue
            bundle[name] = read_json(path)
        if missing:
            raise FileNotFoundError(
                "Fixtures GA4 manquantes. Lance d'abord :\n"
                "  python main.py generate-ga4-fixtures\n"
                "Fichiers absents :\n  - " + "\n  - ".join(missing)
            )
        return bundle
