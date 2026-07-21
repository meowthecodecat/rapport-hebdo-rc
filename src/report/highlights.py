"""
Generateur de "Highlights" : detecte les ecarts significatifs vs LW/LY
(sessions globales, canaux de trafic, top pages, et cote e-commerce
units/net sales) et les formule en texte.

Choix de conception important : tout est explicitement presente comme
un DRAFT a valider par un humain, jamais comme une affirmation ("est du
a...") - on ne connait pas la cause reelle d'un ecart a partir des seuls
chiffres GA4/Shopify. Le but est de faire gagner du temps a l'analyste
en pointant OU regarder, pas de remplacer son jugement.

Le seuil (en %) est configurable via config.settings.HIGHLIGHT_THRESHOLD_PCT
ou passe en parametre.
"""

from config.settings import HIGHLIGHT_THRESHOLD_PCT

DRAFT_PREFIX = "[Draft – à valider par un humain]"


def _direction_word(value: float) -> str:
    return "hausse" if value >= 0 else "baisse"


def _fmt_pct(value: float) -> str:
    return f"{value:+.1f}%"


def generate_highlights(ga4: dict, shopify: dict | None = None, threshold_pct: float = HIGHLIGHT_THRESHOLD_PCT) -> list[str]:
    findings: list[str] = []
    summary = ga4["summary"]

    if abs(summary["sessions_vs_lw_pct"]) >= threshold_pct:
        findings.append(
            f"{DRAFT_PREFIX} Sessions globales en {_direction_word(summary['sessions_vs_lw_pct'])} de "
            f"{_fmt_pct(summary['sessions_vs_lw_pct'])} vs la semaine précédente — à confirmer : "
            f"saisonnalité, campagne en cours, ou anomalie de tracking ?"
        )
    if abs(summary["sessions_vs_ly_pct"]) >= threshold_pct:
        findings.append(
            f"{DRAFT_PREFIX} Sessions globales en {_direction_word(summary['sessions_vs_ly_pct'])} de "
            f"{_fmt_pct(summary['sessions_vs_ly_pct'])} vs la même semaine l'an dernier — à valider "
            f"avant diffusion (comparaison sensible aux jours fériés / dates mobiles)."
        )

    for source in ga4["traffic_sources"]:
        if abs(source["sessions_vs_lw_pct"]) >= threshold_pct:
            findings.append(
                f"{DRAFT_PREFIX} Canal « {source['channel']} » en {_direction_word(source['sessions_vs_lw_pct'])} de "
                f"{_fmt_pct(source['sessions_vs_lw_pct'])} vs S-1 ({source['sessions']} sessions, "
                f"{source['pct_of_total']}% du trafic total) — hypothèse à vérifier : changement de "
                f"budget/campagne, mise à jour d'algorithme, ou problème de tracking."
            )

    for page in ga4["top_pages"]:
        if abs(page["sessions_vs_lw_pct"]) >= threshold_pct:
            findings.append(
                f"{DRAFT_PREFIX} Page {page['url']} en {_direction_word(page['sessions_vs_lw_pct'])} de "
                f"{_fmt_pct(page['sessions_vs_lw_pct'])} vs S-1 — à valider : lancement produit, "
                f"couverture presse, ou pic ponctuel ?"
            )
        elif abs(page["sessions_vs_ly_pct"]) >= threshold_pct:
            findings.append(
                f"{DRAFT_PREFIX} Page {page['url']} en {_direction_word(page['sessions_vs_ly_pct'])} de "
                f"{_fmt_pct(page['sessions_vs_ly_pct'])} vs l'an dernier — à valider avant diffusion."
            )

    if shopify is not None:
        shopify_summary = shopify["summary"]
        for key, label in [("units_vs_lw_pct", "Unités vendues"), ("net_sales_vs_lw_pct", "Net sales")]:
            value = shopify_summary[key]
            if abs(value) >= threshold_pct:
                findings.append(
                    f"{DRAFT_PREFIX} {label} en {_direction_word(value)} de {_fmt_pct(value)} vs S-1 — "
                    f"à confirmer avec l'équipe commerciale avant diffusion."
                )

    if not findings:
        findings.append(
            f"{DRAFT_PREFIX} Aucun écart supérieur au seuil de {threshold_pct}% détecté cette semaine "
            f"(vs semaine précédente et vs l'an dernier)."
        )

    return findings
