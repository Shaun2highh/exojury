"""EDA figures for the writeup. Run:  python -m exojury.eda"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import config, data

# Reference palette (dataviz skill), light mode
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
CLASS_COLORS = {
    "CONFIRMED": "#2a78d6",
    "CANDIDATE": "#eda100",
    "FALSE POSITIVE": "#e34948",
}

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


def fig_class_balance(df):
    counts = df[config.TARGET].value_counts()
    fig, ax = plt.subplots(figsize=(7, 3.2))
    order = ["FALSE POSITIVE", "CONFIRMED", "CANDIDATE"]
    y = np.arange(len(order))
    for i, cls in enumerate(order):
        ax.barh(i, counts[cls], height=0.62, color=CLASS_COLORS[cls])
        ax.text(counts[cls] + 60, i, f"{counts[cls]:,}", va="center",
                color=INK2, fontsize=10)
    ax.set_yticks(y, order)
    ax.set_xlabel("KOIs")
    ax.set_title("9,564 Kepler Objects of Interest — what the catalog says",
                 loc="left", fontsize=11, color=INK)
    ax.grid(axis="y", visible=False)
    savefig(fig, "01_class_balance.png")


def fig_period_radius(df):
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    for cls in ["FALSE POSITIVE", "CONFIRMED", "CANDIDATE"]:
        sub = df[df[config.TARGET] == cls]
        ax.scatter(sub["koi_period"], sub["koi_prad"], s=7, alpha=0.45,
                   color=CLASS_COLORS[cls], label=cls, linewidths=0)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Orbital period [days, log]")
    ax.set_ylabel("Planet radius [Earth radii, log]")
    ax.set_title("Period vs radius: false positives dominate the giant-'planet' regime",
                 loc="left", fontsize=11, color=INK)
    ax.axhline(20, color=MUTED, lw=1, ls="--")
    ax.text(0.98, 0.62, "≈ 2 Jupiter radii — larger is almost always a star",
            transform=ax.transAxes, ha="right", fontsize=8, color=INK2,
            bbox=dict(facecolor=SURFACE, edgecolor="none", alpha=0.85, pad=1.5))
    ax.legend(frameon=False, markerscale=2.5, fontsize=9, loc="lower right")
    savefig(fig, "02_period_radius.png")


def fig_feature_separation(df):
    feats = [
        ("koi_model_snr", "Transit signal-to-noise", True),
        ("koi_depth", "Transit depth [ppm]", True),
        ("duty_cycle", "Transit duty cycle", True),
        ("dicco_offset_sig", "Centroid offset significance [σ]", True),
    ]
    df = data.engineer_features(df)
    fig, axes = plt.subplots(2, 2, figsize=(9, 6))
    for ax, (col, label, logx) in zip(axes.ravel(), feats):
        for cls in ["FALSE POSITIVE", "CONFIRMED"]:
            vals = df.loc[df[config.TARGET] == cls, col].dropna()
            vals = vals[vals > 0] if logx else vals
            bins = np.logspace(np.log10(vals.quantile(0.005)),
                               np.log10(vals.quantile(0.995)), 40) if logx else 40
            ax.hist(vals, bins=bins, density=True, alpha=0.55,
                    color=CLASS_COLORS[cls], label=cls)
        if logx:
            ax.set_xscale("log")
        ax.set_xlabel(label, fontsize=9)
        ax.set_yticks([])
        ax.grid(visible=False)
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.suptitle("Where planets and impostors separate (labeled KOIs only)",
                 x=0.02, ha="left", fontsize=11, color=INK)
    savefig(fig, "03_feature_separation.png")


def fig_leakage(df):
    """The money figure: accuracy of 'models' that use leaked columns."""
    from sklearn.metrics import accuracy_score
    rows = []
    pred = np.where(df["kepler_name"].notna(), "CONFIRMED",
             np.where(df["koi_pdisposition"] == "FALSE POSITIVE",
                      "FALSE POSITIVE", "CANDIDATE"))
    rows.append(("kepler_name + koi_pdisposition\n(zero ML, two lines of code)",
                 accuracy_score(df[config.TARGET], pred)))
    anyflag = df[config.VETTING_FLAG_COLS].sum(axis=1) > 0
    lab = df[df[config.TARGET] != "CANDIDATE"]
    pred2 = np.where(anyflag[lab.index], "FALSE POSITIVE", "CONFIRMED")
    rows.append(("Robovetter fpflags only\n(zero ML, binary task)",
                 accuracy_score(lab[config.TARGET], pred2)))
    fig, ax = plt.subplots(figsize=(7.5, 3))
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    ax.barh(range(len(rows)), vals, height=0.55, color="#e34948")
    for i, v in enumerate(vals):
        ax.text(v - 0.005, i, f"{v*100:.2f}%", va="center", ha="right",
                color="#ffffff", fontsize=11, fontweight="bold")
    ax.set_yticks(range(len(rows)), labels, fontsize=9)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Accuracy")
    ax.set_title("The answer key hiding in the dataset — why our model excludes these columns",
                 loc="left", fontsize=11, color=INK)
    ax.grid(axis="y", visible=False)
    savefig(fig, "04_leakage_answer_key.png")


def main():
    df = data.load_raw()
    fig_class_balance(df)
    fig_period_radius(df)
    fig_feature_separation(df)
    fig_leakage(df)
    print("EDA figures written to reports/figures/")


if __name__ == "__main__":
    main()
