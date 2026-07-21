"""
Helpers de calendrier pour le rapport hebdomadaire.

Convention retenue : une "semaine de reporting" va du lundi au dimanche
(ISO). Le rapport porte toujours sur la dernière semaine ENTIEREMENT
terminee avant la date du jour (jamais la semaine en cours, incomplete).

"Meme semaine l'an dernier" est calculee a J-364 (52 * 7 jours) plutot
qu'a J-365/366, pour rester alignee sur le meme jour de la semaine
(un lundi tombe sur un lundi) - c'est la convention usuelle des
comparaisons GA4 "vs last year" en semaine calendaire.
"""

from datetime import date, timedelta
from typing import NamedTuple


class WeekRange(NamedTuple):
    start: date
    end: date

    def to_dict(self) -> dict:
        return {"start": self.start.isoformat(), "end": self.end.isoformat()}


def get_current_week_start(today: date | None = None) -> date:
    """Lundi de la derniere semaine complete avant `today`."""
    today = today or date.today()
    monday_of_today_week = today - timedelta(days=today.weekday())
    return monday_of_today_week - timedelta(days=7)


def week_range(week_start: date) -> WeekRange:
    return WeekRange(start=week_start, end=week_start + timedelta(days=6))


def previous_week_start(week_start: date) -> date:
    return week_start - timedelta(days=7)


def same_week_last_year_start(week_start: date) -> date:
    return week_start - timedelta(days=364)


def build_period(today: date | None = None) -> dict:
    """Bloc 'period' complet tel qu'ecrit dans les JSON mock GA4/Shopify.

    MOCK -> REEL : en prod, ces trois plages seraient simplement les
    parametres startDate/endDate envoyes a la GA4 Data API (runReport)
    et aux filtres de date de la Shopify Admin API, sans rien changer
    au reste du pipeline (join, highlights, rapport).
    """
    current_start = get_current_week_start(today)
    previous_start = previous_week_start(current_start)
    ly_start = same_week_last_year_start(current_start)
    return {
        "current_week": week_range(current_start).to_dict(),
        "previous_week": week_range(previous_start).to_dict(),
        "same_week_last_year": week_range(ly_start).to_dict(),
    }


def iter_weeks_back(week_start: date, count: int) -> list[date]:
    """Liste de `count` lundis, du plus ancien au plus recent, se terminant a `week_start`."""
    return [week_start - timedelta(days=7 * i) for i in range(count - 1, -1, -1)]
