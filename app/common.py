"""Shared data loading, constants and helpers for all pages."""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exojury import config, data  # noqa: E402

PANEL = "#101216"
INK = "#ffffff"
INK2 = "#c3c2b7"
MUTED = "#8a8f98"
GRID = "#23262d"
BLUE = "#3987e5"
VIOLET = "#9085e9"
YELLOW = "#c98500"
RED = "#e66767"

VERDICT_STYLE = {
    "CONFIRMED": (BLUE, "PLANET"),
    "FALSE POSITIVE": (RED, "FALSE POSITIVE"),
    "NEEDS REVIEW (ambiguous)": (YELLOW, "NEEDS REVIEW"),
    "NEEDS REVIEW (both plausible)": (YELLOW, "NEEDS REVIEW"),
}
CATALOG_COLOR = {"CONFIRMED": BLUE, "CANDIDATE": YELLOW, "FALSE POSITIVE": RED}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=PANEL, plot_bgcolor=PANEL,
    font=dict(color=INK2, family="Space Grotesk, system-ui, sans-serif", size=12),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#31353d"),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#31353d"),
    margin=dict(l=10, r=10, t=30, b=10),
)

LITERATURE = {
    "K01450.01": ("Verified catch", RED,
        "Catalog snapshot says CONFIRMED (Kepler-854 b). NASA <b>demoted it "
        "to false positive</b> after Niraula et al. 2022 revised its mass "
        "above 30 M_Jup. ExoJury flagged it at p = 0.00003 from this CSV alone."),
    "K01416.01": ("Verified catch", RED,
        "Catalog snapshot says CONFIRMED (Kepler-840 b). Also <b>demoted by "
        "NASA</b> after the same 2022 mass revision. ExoJury: p = 0.0016."),
    "K07016.01": ("Disputed in literature", YELLOW,
        "Kepler-452 b, 'Earth's cousin'. Its statistical validation was "
        "formally disputed (Mullally et al. 2018); with final DR25 data it "
        "no longer reaches 99% confidence. ExoJury: p = 0.0006."),
    "K03794.01": ("Honest miss", YELLOW,
        "Kepler-1520 b — a real but <i>disintegrating</i> planet. Its dusty, "
        "variable transits break the standard fit (fitted radius 23 R⊕), so "
        "the model scores it low. Physics weirder than the training set."),
    "K00701.03": ("Showpiece", BLUE,
        "Kepler-62 e — a confirmed super-Earth in the habitable zone, "
        "1.7 R⊕ at 270 K. ExoJury agrees with the catalog at >99.9%."),
}


def rgba(hex_color: str, a: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{a})"


@st.cache_resource
def load_artifacts():
    bundle = joblib.load(config.MODELS_DIR / "calibrated_conformal.joblib")
    scores = pd.read_csv(config.REPORTS_DIR / "scores_all.csv")
    audit = pd.read_csv(config.REPORTS_DIR / "label_audit.csv")
    return bundle, scores, audit


@st.cache_data
def class_percentiles(feature: str):
    _, scores, _ = load_artifacts()
    pl = np.sort(scores.loc[scores.catalog == "CONFIRMED", feature].dropna().values)
    fp = np.sort(scores.loc[scores.catalog == "FALSE POSITIVE", feature].dropna().values)
    return pl, fp


def nasa_url(kepoi: str) -> str:
    star, planet = kepoi[1:].split(".")
    return f"https://exoplanetarchive.ipac.caltech.edu/overview/KOI-{int(star)}.{planet}"


def spectral_class(teff) -> str:
    if pd.isna(teff):
        return "?"
    for limit, letter in [(3900, "M"), (5300, "K"), (6000, "G"), (7500, "F"),
                          (10000, "A")]:
        if teff < limit:
            return letter
    return "B"


def section(eyebrow: str, title: str, sub: str = "") -> None:
    """Minimal section header: small-caps eyebrow + title + optional sub."""
    st.markdown(
        f'<div class="sect"><div class="eyebrow">{eyebrow}</div>'
        f'<div class="sect-title">{title}</div>'
        + (f'<div class="sect-sub">{sub}</div>' if sub else "")
        + "</div>", unsafe_allow_html=True)
