"""
Graphiques rendus en SVG natif (aucune dependance JS), pour que le
rapport HTML s'affiche et s'imprime en PDF (via Playwright) sans acces
reseau ni librairie externe a charger.

Palette et regles de conception suivent le skill data-viz du projet
(palette categorielle validee CVD-safe, une seule teinte pour le
sequentiel, jamais de double axe, legende obligatoire des que 2 series,
etiquettes directes sujettes a moderation, grille en trait fin recessif).

Deux graphiques :
- render_trend_chart   : courbe L6M "cette annee" (accent) vs "annee
  precedente" (gris pointille) - traitement "emphasis" : une serie est
  le sujet, l'autre sert de reference.
- render_traffic_donut  : donut Traffic Sources. Les 8 canaux principaux
  gardent chacun une couleur fixe (memes couleurs d'un marche/d'une
  semaine a l'autre - l'identite suit le canal, jamais son rang), les 2
  canaux residuels (Unassigned, Cross-network) sont regroupes en
  "Other" (gris neutre) pour rester lisible a l'oeil sur un donut a 10
  parts. Le detail exact des 10 canaux reste disponible dans la table
  qui accompagne le graphique (cf. templates) - rien n'est cache, juste
  regroupe visuellement.
"""

import math

# --- Chrome (fond, encre, grille) - references/palette.md ---
CHROME = {
    "light": {
        "surface": "#fcfcfb", "primary": "#0b0b0b", "secondary": "#52514e",
        "muted": "#898781", "gridline": "#e1e0d9", "baseline": "#c3c2b7",
    },
    "dark": {
        "surface": "#1a1a19", "primary": "#ffffff", "secondary": "#c3c2b7",
        "muted": "#898781", "gridline": "#2c2c2a", "baseline": "#383835",
    },
}

# --- Palette categorielle validee (8 teintes, ordre fixe = mecanisme CVD-safe) ---
CATEGORICAL_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
CATEGORICAL_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]

# Mapping fixe canal -> slot de couleur (jamais recalcule selon le rang du canal).
CHANNEL_COLOR_ORDER = [
    "Organic Search", "Paid Social", "Direct", "Organic Social",
    "Paid Search", "Referral", "Email", "Display",
]
OTHER_CHANNELS = {"Unassigned", "Cross-network"}


def _channel_color(channel: str, mode: str = "light") -> str:
    palette = CATEGORICAL_LIGHT if mode == "light" else CATEGORICAL_DARK
    if channel in CHANNEL_COLOR_ORDER:
        return palette[CHANNEL_COLOR_ORDER.index(channel)]
    return CHROME[mode]["muted"]  # "Other" et tout canal imprevu


def _fmt_number(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value / 1000:.1f}K".replace(".0K", "K")
    return f"{value:.0f}"


def render_trend_chart(trend_6m: list[dict], width: int = 640, height: int = 260) -> str:
    """Courbe L6M vs LY. Une <title> par point sert de tooltip natif
    (pas de JS) au survol dans un navigateur qui le supporte."""
    pad_left, pad_right, pad_top, pad_bottom = 48, 54, 16, 28
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    current = [p["sessions"] for p in trend_6m]
    ly = [p["sessions_ly"] for p in trend_6m]
    all_values = current + ly
    v_min, v_max = 0, max(all_values) * 1.08
    n = len(trend_6m)

    def x_at(i: int) -> float:
        return pad_left + (plot_w * i / (n - 1))

    def y_at(v: float) -> float:
        return pad_top + plot_h - (plot_h * (v - v_min) / (v_max - v_min))

    light, dark = CHROME["light"], CHROME["dark"]

    # Grille horizontale (3 paliers, trait fin, jamais pointille).
    grid_svg = []
    for step in range(4):
        v = v_min + (v_max - v_min) * step / 3
        y = y_at(v)
        grid_svg.append(
            f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" '
            f'class="viz-grid" />'
            f'<text x="{pad_left - 8}" y="{y + 4:.1f}" text-anchor="end" class="viz-axis-label">{_fmt_number(v)}</text>'
        )

    # Ticks de mois en abscisse (change de mois -> libelle court).
    month_ticks = []
    last_month = None
    for i, point in enumerate(trend_6m):
        month = point["week_start"][:7]  # YYYY-MM
        if month != last_month:
            month_ticks.append((i, point["week_start"]))
            last_month = month
    month_labels_svg = []
    for i, week_start in month_ticks:
        label = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"][int(week_start[5:7]) - 1]
        month_labels_svg.append(
            f'<text x="{x_at(i):.1f}" y="{height - 6}" text-anchor="middle" class="viz-axis-label">{label}</text>'
        )

    def polyline(values: list[float]) -> str:
        return " ".join(f"{x_at(i):.1f},{y_at(v):.1f}" for i, v in enumerate(values))

    def point_titles(values: list[float], series_label: str) -> str:
        out = []
        for i, v in enumerate(values):
            week = trend_6m[i]["week_start"]
            out.append(
                f'<circle cx="{x_at(i):.1f}" cy="{y_at(v):.1f}" r="7" fill="transparent">'
                f'<title>{series_label} · semaine du {week} · {v:,} sessions</title></circle>'
            )
        return "".join(out)

    last_i = n - 1
    end_label_current = f'<text x="{x_at(last_i) + 6:.1f}" y="{y_at(current[-1]) - 6:.1f}" class="viz-end-label viz-accent-text">{_fmt_number(current[-1])}</text>'
    end_label_ly = f'<text x="{x_at(last_i) + 6:.1f}" y="{y_at(ly[-1]) + 14:.1f}" class="viz-end-label viz-muted-text">{_fmt_number(ly[-1])}</text>'

    svg = f"""
<svg class="viz-root viz-trend" viewBox="0 0 {width} {height}" width="100%" height="auto" role="img"
     aria-label="Évolution des sessions sur 6 mois, comparée à l'année précédente">
  <style>
    .viz-trend {{ color-scheme: light; }}
    .viz-trend {{ --surface: {light['surface']}; --grid: {light['gridline']}; --muted: {light['muted']}; --secondary: {light['secondary']}; --accent: {_channel_color('Organic Search','light')}; }}
    @media (prefers-color-scheme: dark) {{
      :root:where(:not([data-theme="light"])) .viz-trend {{ --surface: {dark['surface']}; --grid: {dark['gridline']}; --muted: {dark['muted']}; --secondary: {dark['secondary']}; --accent: {_channel_color('Organic Search','dark')}; }}
    }}
    :root[data-theme="dark"] .viz-trend {{ --surface: {dark['surface']}; --grid: {dark['gridline']}; --muted: {dark['muted']}; --secondary: {dark['secondary']}; --accent: {_channel_color('Organic Search','dark')}; }}
    .viz-trend .viz-grid {{ stroke: var(--grid); stroke-width: 1; }}
    .viz-trend .viz-axis-label {{ fill: var(--muted); font-size: 11px; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
    .viz-trend .viz-end-label {{ font-size: 12px; font-weight: 600; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
    .viz-trend .viz-accent-text {{ fill: var(--accent); }}
    .viz-trend .viz-muted-text {{ fill: var(--secondary); }}
    .viz-trend .viz-line-current {{ fill: none; stroke: var(--accent); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }}
    .viz-trend .viz-line-ly {{ fill: none; stroke: var(--muted); stroke-width: 2; stroke-dasharray: 5 4; stroke-linecap: round; }}
    .viz-trend .viz-dot-current {{ fill: var(--accent); stroke: var(--surface); stroke-width: 2; }}
    .viz-trend .viz-dot-ly {{ fill: var(--muted); stroke: var(--surface); stroke-width: 2; }}
  </style>
  <rect x="0" y="0" width="{width}" height="{height}" fill="var(--surface)" />
  {''.join(grid_svg)}
  {''.join(month_labels_svg)}
  <polyline class="viz-line-ly" points="{polyline(ly)}" />
  <polyline class="viz-line-current" points="{polyline(current)}" />
  <circle class="viz-dot-current" cx="{x_at(last_i):.1f}" cy="{y_at(current[-1]):.1f}" r="4" />
  <circle class="viz-dot-ly" cx="{x_at(last_i):.1f}" cy="{y_at(ly[-1]):.1f}" r="4" />
  {end_label_current}
  {end_label_ly}
  {point_titles(current, "Cette année")}
  {point_titles(ly, "Année précédente")}
</svg>
""".strip()
    return svg


def render_traffic_donut(traffic_sources: list[dict], width: int = 300, height: int = 300) -> str:
    """Donut Traffic Sources : 8 canaux nommés + 1 part 'Other' (2 canaux
    residuels regroupes). Legende + libelles directs sur les parts >= 8%."""
    total = sum(s["sessions"] for s in traffic_sources)
    named = [s for s in traffic_sources if s["channel"] not in OTHER_CHANNELS]
    other_sessions = sum(s["sessions"] for s in traffic_sources if s["channel"] in OTHER_CHANNELS)
    named.sort(key=lambda s: s["sessions"], reverse=True)

    slices = [{"channel": s["channel"], "sessions": s["sessions"]} for s in named]
    if other_sessions:
        slices.append({"channel": "Other", "sessions": other_sessions})

    cx, cy = width / 2, height / 2 - 6
    r_outer = min(width, height) / 2 - 34
    r_inner = r_outer * 0.6

    def point_on_circle(radius: float, angle_deg: float) -> tuple[float, float]:
        angle_rad = math.radians(angle_deg - 90)
        return cx + radius * math.cos(angle_rad), cy + radius * math.sin(angle_rad)

    paths_svg = []
    labels_svg = []
    legend_rows = []
    angle = 0.0
    for slot in slices:
        share = slot["sessions"] / total
        sweep = share * 360
        start_angle, end_angle = angle, angle + sweep
        large_arc = 1 if sweep > 180 else 0

        outer_start = point_on_circle(r_outer, start_angle)
        outer_end = point_on_circle(r_outer, end_angle)
        inner_start = point_on_circle(r_inner, start_angle)
        inner_end = point_on_circle(r_inner, end_angle)

        pct_label = f"{share * 100:.1f}%"

        # Secteur annulaire : arc exterieur (start->end, sens horaire),
        # ligne radiale vers le cercle interieur, arc interieur retour
        # (end->start, sens anti-horaire), puis Z referme la ligne
        # radiale de depart. Les deux arcs doivent parcourir le meme
        # angle en sens opposes pour former un vrai secteur plein - les
        # inverser produit un "petale" en croisant les diagonales.
        path_d = (
            f"M {outer_start[0]:.2f},{outer_start[1]:.2f} "
            f"A {r_outer:.2f},{r_outer:.2f} 0 {large_arc} 1 {outer_end[0]:.2f},{outer_end[1]:.2f} "
            f"L {inner_end[0]:.2f},{inner_end[1]:.2f} "
            f"A {r_inner:.2f},{r_inner:.2f} 0 {large_arc} 0 {inner_start[0]:.2f},{inner_start[1]:.2f} Z"
        )
        css_class = f"slice-{len(paths_svg)}"
        paths_svg.append(
            f'<path d="{path_d}" class="viz-slice {css_class}"><title>{slot["channel"]} · {slot["sessions"]:,} sessions ({pct_label})</title></path>'
        )
        # slice styling injected per-index (light/dark) below in <style>.
        legend_rows.append((slot["channel"], pct_label, css_class))

        if share >= 0.08:
            mid_angle = (start_angle + end_angle) / 2
            lx, ly_ = point_on_circle((r_outer + r_inner) / 2, mid_angle)
            labels_svg.append(
                f'<text x="{lx:.1f}" y="{ly_:.1f}" text-anchor="middle" dominant-baseline="middle" class="viz-slice-label">{pct_label}</text>'
            )
        angle = end_angle

    def slice_rules(mode: str, scope: str = ".viz-donut") -> str:
        return "\n".join(
            f'{scope} .slice-{i} {{ fill: {_channel_color(ch, mode)}; }}'
            for i, (ch, _, _) in enumerate(legend_rows)
        )

    legend_html = "".join(
        f'<li><span class="viz-swatch slice-{i}"></span>{ch} <span class="viz-legend-pct">{pct}</span></li>'
        for i, (ch, pct, _) in enumerate(legend_rows)
    )

    light, dark = CHROME["light"], CHROME["dark"]
    svg = f"""
<div class="viz-root viz-donut">
  <style>
    .viz-donut {{ color-scheme: light; --surface: {light['surface']}; --primary: {light['primary']}; --secondary: {light['secondary']}; }}
    :root[data-theme="dark"] .viz-donut {{ --surface: {dark['surface']}; --primary: {dark['primary']}; --secondary: {dark['secondary']}; }}
    .viz-donut .viz-slice {{ stroke: var(--surface); stroke-width: 2; stroke-linejoin: round; }}
    .viz-donut .viz-slice-label {{ font-size: 11px; font-weight: 600; fill: #ffffff; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
    .viz-donut ul.viz-legend {{ list-style: none; margin: 8px 0 0; padding: 0; font-size: 13px; color: var(--secondary); display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; }}
    .viz-donut .viz-legend-pct {{ color: var(--secondary); font-variant-numeric: tabular-nums; }}
    .viz-donut .viz-swatch {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; }}
    {slice_rules("light")}
    @media (prefers-color-scheme: dark) {{
      :root:where(:not([data-theme="light"])) .viz-donut {{ --surface: {dark['surface']}; --primary: {dark['primary']}; --secondary: {dark['secondary']}; }}
      {slice_rules("dark", ':root:where(:not([data-theme="light"])) .viz-donut')}
    }}
    {slice_rules("dark", ':root[data-theme="dark"] .viz-donut')}
  </style>
  <svg viewBox="0 0 {width} {height}" width="100%" height="auto" role="img" aria-label="Répartition des sessions par canal de trafic">
    {''.join(paths_svg)}
    {''.join(labels_svg)}
  </svg>
  <ul class="viz-legend">{legend_html}</ul>
</div>
""".strip()
    return svg
