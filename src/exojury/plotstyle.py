"""Shared matplotlib palette: light (README/GitHub) and dark (app) modes.

Values are the dataviz reference palette's light/dark steps, so static
figures match the dashboard exactly.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

LIGHT = dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781",
             grid="#e1e0d9", edge="#c3c2b7",
             blue="#2a78d6", yellow="#eda100", red="#e34948")
DARK = dict(surface="#1a1a19", ink="#ffffff", ink2="#c3c2b7", muted="#898781",
            grid="#2c2c2a", edge="#383835",
            blue="#3987e5", yellow="#c98500", red="#e66767")


def apply(dark: bool = False) -> dict:
    """Set rcParams for the mode and return its palette."""
    p = DARK if dark else LIGHT
    plt.rcParams.update({
        "figure.facecolor": p["surface"], "axes.facecolor": p["surface"],
        "savefig.facecolor": p["surface"],
        "axes.edgecolor": p["edge"], "axes.labelcolor": p["ink2"],
        "text.color": p["ink"], "xtick.color": p["muted"],
        "ytick.color": p["muted"],
        "axes.grid": True, "grid.color": p["grid"], "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "font.family": "sans-serif", "figure.dpi": 150,
    })
    return p


def mode_from_argv(argv) -> bool:
    return "--dark" in argv
