"""Petits helpers aleatoires partages entre generate_ga4.py et generate_shopify.py."""

import random


def pct(rng: random.Random, low: float, high: float) -> float:
    return round(rng.uniform(low, high), 1)


def delta_with_occasional_outlier(rng: random.Random, outlier_chance: float = 0.18) -> float:
    """Ecart vs LW/LY : la plupart du temps un bruit normal, parfois un
    vrai mouvement (>15%) pour alimenter les highlights de facon realiste."""
    if rng.random() < outlier_chance:
        sign = rng.choice([-1, 1])
        return sign * round(rng.uniform(16, 38), 1)
    return pct(rng, -12, 12)
