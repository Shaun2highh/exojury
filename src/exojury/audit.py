"""Stage 3: audit NASA's own labels with confident learning.

Uses cleanlab to find KOIs whose catalog disposition disagrees strongly
with out-of-fold model predictions — i.e. entries that may be mislabeled
(or at least deserve a second look). This flips the usual framing: instead
of only trusting labels to judge the model, we use the model to interrogate
the labels.

Run:  python -m exojury.audit
"""

import numpy as np
import pandas as pd
from cleanlab.filter import find_label_issues
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from . import config, data
from .train_baseline import make_model


def main():
    df = data.load_raw()
    labeled, _ = data.split_labeled_candidates(df)
    X = data.build_features(labeled)
    y = labeled[config.TARGET].map(config.LABEL_MAP_BINARY).values

    # Out-of-fold predicted probabilities over ALL labeled rows: every row
    # is scored by a model that never saw it.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.SEED)
    proba = cross_val_predict(make_model(), X, y, cv=cv, method="predict_proba")

    issue_idx = find_label_issues(
        labels=y, pred_probs=proba, return_indices_ranked_by="self_confidence"
    )
    print(f"cleanlab flags {len(issue_idx)} of {len(y)} labeled KOIs "
          f"({len(issue_idx)/len(y)*100:.1f}%) as potential label issues\n")

    out = labeled.iloc[issue_idx][
        ["kepoi_name", "kepler_name", "koi_disposition",
         "koi_period", "koi_prad", "koi_model_snr"]
    ].copy()
    out["p_planet_oof"] = proba[issue_idx, 1]
    config.REPORTS_DIR.mkdir(exist_ok=True)
    out.to_csv(config.REPORTS_DIR / "label_audit.csv", index=False)

    print("Top 15 most suspicious labels (model most confidently disagrees):")
    print(out.head(15).to_string(index=False))
    print("\nSaved full list to reports/label_audit.csv")
    print("Next step: cross-check the top few against the literature "
          "(NASA Exoplanet Archive overview pages) before making claims.")


if __name__ == "__main__":
    main()
