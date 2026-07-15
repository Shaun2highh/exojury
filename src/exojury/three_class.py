"""Challenge-required 3-class metrics (CONFIRMED / CANDIDATE / FALSE POSITIVE).

We argue the binary task + candidate scoring is the scientifically right
framing (CANDIDATE is an "unknown", not a class of object). But the challenge
guide asks for the 3-class treatment, so here it is, leakage-free.

Run:  python -m exojury.three_class
"""

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from . import config, data


def main():
    df = data.load_raw()
    y = df[config.TARGET].map(config.LABEL_MAP_3CLASS).values
    X = data.build_features(df)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=config.SEED
    )
    model = HistGradientBoostingClassifier(
        max_iter=250, learning_rate=0.08, max_leaf_nodes=31,
        l2_regularization=1.0, early_stopping=True, validation_fraction=0.1,
        n_iter_no_change=25, random_state=config.SEED,
    ).fit(X_tr, y_tr)

    pred = model.predict(X_te)
    names = ["FALSE POSITIVE", "CANDIDATE", "CONFIRMED"]
    print(classification_report(y_te, pred, target_names=names, digits=3))

    cm = confusion_matrix(y_te, pred)
    print("Confusion matrix (rows=true, cols=pred):")
    print(cm)

    # Figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(3), names, rotation=20, fontsize=8)
    ax.set_yticks(range(3), names, fontsize=8)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{cm[i,j]:,}", ha="center", va="center", fontsize=11,
                    color="white" if cm[i, j] > cm.max() / 2 else "#0b0b0b")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("3-class confusion matrix — honest features, held-out test",
                 loc="left", fontsize=10)
    fig.colorbar(im, shrink=0.8)
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "05_confusion_3class.png", dpi=150,
                bbox_inches="tight")
    print("saved reports/figures/05_confusion_3class.png")


if __name__ == "__main__":
    main()
