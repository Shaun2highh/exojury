"""Calibration + conformal figures from saved artifacts (no retraining).

Run:  python -m exojury.figures_stage2
"""

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config, data
from .calibrate import conformal_sets, reliability_table

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BLUE = "#2a78d6"
YELLOW = "#eda100"
RED = "#e34948"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
    "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "sans-serif", "figure.dpi": 150,
})


def savefig(fig, name):
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / name, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {name}")


def main():
    raw_bundle = joblib.load(config.MODELS_DIR / "baseline_honest.joblib")
    cal_bundle = joblib.load(config.MODELS_DIR / "calibrated_conformal.joblib")
    test_df = pd.read_csv(config.MODELS_DIR / "test_split.csv")
    y_test = test_df[config.TARGET].map(config.LABEL_MAP_BINARY).values
    X_test = data.build_features(test_df)[cal_bundle["features"]]

    p_raw = raw_bundle["model"].predict_proba(X_test)[:, 1]
    p_cal = cal_bundle["model"].predict_proba(X_test)[:, 1]

    # --- reliability diagram ---
    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--", zorder=1)
    for p, color, label in [(p_raw, YELLOW, "Uncalibrated"),
                            (p_cal, BLUE, "Isotonic calibrated")]:
        tab = reliability_table(y_test, p, n_bins=5)
        # marker area tracks bin population: noisy 6-object bins stay small
        sizes = 30 + 300 * np.sqrt(tab["n"] / tab["n"].max())
        ax.plot(tab["mean_predicted"], tab["observed_rate"], "-",
                color=color, lw=1.5, label=label, zorder=2)
        ax.scatter(tab["mean_predicted"], tab["observed_rate"], s=sizes,
                   color=color, zorder=3, linewidths=0)
    ax.set_xlabel("Mean predicted planet probability")
    ax.set_ylabel("Observed planet fraction")
    ax.set_title("When ExoJury says 90%, it happens ~90% of the time",
                 loc="left", fontsize=10, color=INK)
    ax.text(0.98, 0.02, "marker size = objects per bin",
            transform=ax.transAxes, ha="right", fontsize=8, color=MUTED)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    savefig(fig, "06_reliability.png")

    # --- conformal verdicts: test set vs candidate frontier ---
    sets_test = conformal_sets(p_cal, cal_bundle["qhat"])
    scores = pd.read_csv(config.REPORTS_DIR / "candidate_scores.csv")
    order = ["CONFIRMED", "FALSE POSITIVE", "NEEDS REVIEW (ambiguous)",
             "NEEDS REVIEW (both plausible)"]
    short = {"CONFIRMED": "Planet", "FALSE POSITIVE": "False positive",
             "NEEDS REVIEW (ambiguous)": "Needs review",
             "NEEDS REVIEW (both plausible)": "Needs review"}
    verdict_colors = {"Planet": BLUE, "False positive": RED,
                      "Needs review": YELLOW}

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharex=True)
    for ax, (title, series) in zip(axes, [
        ("Labeled test set (n=1,518)", sets_test),
        ("Unresolved CANDIDATEs (n=1,978)", scores["conformal_verdict"]),
    ]):
        counts = series.map(short).value_counts()
        cats = ["Planet", "False positive", "Needs review"]
        vals = [counts.get(c, 0) for c in cats]
        total = sum(vals)
        ax.barh(range(len(cats)), vals, height=0.6,
                color=[verdict_colors[c] for c in cats])
        for i, v in enumerate(vals):
            ax.text(v + total * 0.01, i, f"{v:,}  ({v/total*100:.0f}%)",
                    va="center", fontsize=9, color=INK2)
        ax.set_yticks(range(len(cats)), cats, fontsize=9)
        ax.set_xlim(0, max(vals) * 1.3)
        ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
    fig.suptitle("Conformal verdicts at 95% coverage — the model knows when it doesn't know",
                 x=0.02, ha="left", fontsize=11, color=INK)
    savefig(fig, "07_conformal_verdicts.png")


if __name__ == "__main__":
    main()
