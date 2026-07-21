"""
Client GA4 reel (stub plug-and-play).

Quand tu auras un service account + property IDs :
1. pip install google-analytics-data
2. Renseigner GA4_PROPERTY_IDS + GOOGLE_APPLICATION_CREDENTIALS
3. Passer GA4_MODE = "real" dans config/settings.py
4. Completer les appels run_report ci-dessous (TODO marques)

La signature de `fetch_reports` DOIT rester identique a MockGa4Client :
meme cles de bundle (summary / top_pages / traffic_sources / trend_6m),
meme forme de reponse runReport, pour que normalize.py ne change pas.
"""

from __future__ import annotations

from config.settings import GA4_PROPERTY_IDS


class RealGa4Client:
    def fetch_reports(self, market_code: str, period: dict) -> dict[str, dict]:
        property_id = GA4_PROPERTY_IDS.get(market_code)
        if not property_id or property_id.startswith("REPLACE_"):
            raise NotImplementedError(
                f"Property GA4 non configuree pour {market_code}. "
                f"Renseigne GA4_PROPERTY_IDS['{market_code}'] dans config/settings.py "
                "(ex: 'properties/123456789'), puis implemente les appels run_report "
                "dans src/ga4/real_client.py."
            )

        # TODO (passage reel) — pseudo-code a brancher :
        #
        # from google.analytics.data_v1beta import BetaAnalyticsDataClient
        # from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
        #
        # client = BetaAnalyticsDataClient()
        # current = period["current_week"]
        # previous = period["previous_week"]
        # ly = period["same_week_last_year"]
        #
        # summary = client.run_report(RunReportRequest(
        #     property=property_id,
        #     date_ranges=[
        #         DateRange(start_date=current["start"], end_date=current["end"]),
        #         DateRange(start_date=previous["start"], end_date=previous["end"]),
        #         DateRange(start_date=ly["start"], end_date=ly["end"]),
        #     ],
        #     metrics=[
        #         Metric(name="sessions"),
        #         Metric(name="sessionConversionRate"),
        #     ],
        # ))
        # ... idem top_pages / traffic_sources / trend_6m ...
        # return {
        #     "summary": MessageToDict(summary),
        #     "top_pages": ...,
        #     "traffic_sources": ...,
        #     "trend_6m": ...,
        # }
        #
        # Astuce : dump un vrai runReport une fois, place-le dans
        # data/fixtures/ga4/<market>/ pour comparer le shape avec les mocks.

        raise NotImplementedError(
            "RealGa4Client n'est pas encore branche sur l'API. "
            "Garde GA4_MODE='mock' pour la PoC, ou complete les appels "
            f"run_report pour la property {property_id}."
        )
