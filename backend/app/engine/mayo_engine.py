"""
M.A.N.D.I. Engine — Mayonnaise Analysis & Nutrition Determination Interface

Calculates the "scientifically unnecessary" amount of mayonnaise needed
for a given quantity and characteristics of mandi rice.
"""

from dataclasses import dataclass
from typing import Optional

# 1 part mayonnaise : 4 parts mandi rice
BASE_RATIO = 4.0

SPICE_FACTORS = {
    "mild": 0.85,
    "medium": 1.00,
    "spicy": 1.20,
    "nuclear": 1.50,
}

DRYNESS_FACTORS = {
    "moist": 0.85,
    "normal": 1.00,
    "dry": 1.15,
    "sahara": 1.35,
}

MAYO_FACTORS = {
    "minimal": 0.75,
    "balanced": 1.00,
    "lover": 1.25,
    "criminal": 1.60,
}

# Tablespoons to grams conversion (approximate, mayo density varies)
GramsPerTbsp = 14.0


@dataclass
class CalculationBreakdown:
    rice_grams: float
    base_mayo: float
    spice_factor: float
    dryness_factor: float
    preference_factor: float
    recommended_mayo: float
    ratio: str
    tablespoons: int
    uselessness_score: int
    spice_label: str
    dryness_label: str
    preference_label: str


@dataclass
class MayoRecommendation:
    rice_grams: float
    base_mayo: float
    spice_factor: float
    dryness_factor: float
    preference_factor: float
    recommended_mayo_grams: float
    ratio: str
    tablespoons: int
    uselessness_score: int
    breakdown: list[dict]
    verdict: str
    verdict_color: str


def _tbsp(grams: float) -> int:
    return round(grams / GramsPerTbsp)


def _ratio(rice: float, mayo: float) -> str:
    if mayo == 0:
        return "1 : ∞"
    r = rice / mayo
    return f"1 : {r:.2f}"


def _uselessness_score(
    spice_label: str,
    dryness_label: str,
    preference_label: str,
    ratio_waste: float,
) -> int:
    """
    A completely meaningless number between 0 and 100.
    Higher = more useless.
    """
    spice_score = {"mild": 10, "medium": 20, "spicy": 30, "nuclear": 50}.get(
        spice_label, 20
    )
    dryness_score = {
        "moist": 5,
        "normal": 10,
        "dry": 20,
        "sahara": 40,
    }.get(dryness_label, 10)
    pref_score = {
        "minimal": 30,
        "balanced": 20,
        "lover": 60,
        "criminal": 90,
    }.get(preference_label, 20)

    score = spice_score + dryness_score + pref_score + ratio_waste
    return min(100, max(0, int(score)))


def _overdose_verdict(rice: float, mayo: float) -> tuple[str, str]:
    """
    Classify the mayo-to-rice ratio.
    """
    ratio_val = mayo / rice if rice > 0 else float("inf")

    if ratio_val > 0.5:
        # mayo > rice/2 → 1:2 or worse
        return "🚨 MAYO OVERDOSE — Mandi is now the side dish. Mayonnaise is the main course.", "red"
    elif ratio_val > 0.333:
        return "⚠️ MAYO HEAVY — This is starting to look like a mayo salad.", "orange"
    elif ratio_val > 0.2:
        return "✅ BALANCED — You monster. In the best way.", "green"
    else:
        return "🥶 MAYO CONSERVATIVE — Are you sure this is mandi?", "blue"


def calculate_mayo(
    rice_grams: float,
    spice_level: str = "medium",
    dryness: str = "normal",
    mayo_preference: str = "balanced",
) -> MayoRecommendation:
    """
    Core M.A.N.D.I. algorithm:

    base_mayo = rice / BASE_RATIO
    recommended = base × spice × dryness × preference
    """
    spice_factor = SPICE_FACTORS.get(spice_level, 1.00)
    dryness_factor = DRYNESS_FACTORS.get(dryness, 1.00)
    preference_factor = MAYO_FACTORS.get(mayo_preference, 1.00)

    base_mayo = rice_grams / BASE_RATIO
    recommended = base_mayo * spice_factor * dryness_factor * preference_factor

    recommended = round(recommended, 1)

    tbsp = _tbsp(recommended)
    ratio = _ratio(rice_grams, recommended)

    # Uselessness: how far from a "sane" ratio (1:4) is this?
    sane_mayo = rice_grams / BASE_RATIO
    ratio_waste = abs(recommended - sane_mayo) / max(1, sane_mayo) * 50

    score = _uselessness_score(spice_level, dryness, mayo_preference, int(ratio_waste))

    verdict, verdict_color = _overdose_verdict(rice_grams, recommended)

    breakdown = [
        {"label": "Base requirement", "value": round(base_mayo, 1), "unit": "g"},
        {
            "label": "🌶️ Spice adjustment",
            "value": round(recommended - base_mayo, 1) if spice_factor != 1.0 else 0.0,
            "unit": "g",
        },
        {
            "label": "🏜️ Dryness adjustment",
            "value": round(recommended - base_mayo * spice_factor, 1)
            if dryness_factor != 1.0
            else 0.0,
            "unit": "g",
        },
        {
            "label": "🥄 Mayo preference",
            "value": round(recommended - base_mayo * spice_factor * dryness_factor, 1)
            if preference_factor != 1.0
            else 0.0,
            "unit": "g",
        },
    ]

    return MayoRecommendation(
        rice_grams=rice_grams,
        base_mayo=round(base_mayo, 1),
        spice_factor=spice_factor,
        dryness_factor=dryness_factor,
        preference_factor=preference_factor,
        recommended_mayo_grams=recommended,
        ratio=ratio,
        tablespoons=tbsp,
        uselessness_score=score,
        breakdown=[
            {"step": "Base requirement", "amount": round(base_mayo, 1), "unit": "g"},
            {
                "step": "Spice adjustment",
                "amount": round(base_mayo * (spice_factor - 1), 1),
                "unit": "g",
            },
            {
                "step": "Dryness adjustment",
                "amount": round(base_mayo * spice_factor * (dryness_factor - 1), 1),
                "unit": "g",
            },
            {
                "step": "Mayo preference",
                "amount": round(
                    base_mayo * spice_factor * dryness_factor * (preference_factor - 1), 1
                ),
                "unit": "g",
            },
            {
                "step": "TOTAL",
                "amount": recommended,
                "unit": "g",
            },
        ],
        verdict=verdict,
        verdict_color=verdict_color,
    )


def reverse_calculate(
    mayo_grams: float,
    spice_level: str = "medium",
    dryness: str = "normal",
    mayo_preference: str = "balanced",
) -> float:
    """
    Reverse: given a known amount of mayo, how much mandi rice can be consumed?
    """
    spice_factor = SPICE_FACTORS.get(spice_level, 1.00)
    dryness_factor = DRYNESS_FACTORS.get(dryness, 1.00)
    preference_factor = MAYO_FACTORS.get(mayo_preference, 1.00)

    # recommended = (rice / BASE_RATIO) * spice * dryness * preference
    # => rice = recommended / (spice * dryness * preference) * BASE_RATIO
    rice = (mayo_grams / (spice_factor * dryness_factor * preference_factor)) * BASE_RATIO
    return round(rice, 1)
