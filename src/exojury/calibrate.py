"""Stage 2: trustworthy probabilities and honest uncertainty.

Three layers on top of the baseline classifier:
  1. Probability calibration (isotonic, via cross-validation) — when the
     model says 90%, it should be right ~90% of the time.
  2. Split conformal prediction — per-object prediction *sets* with a
     finite-sample coverage guarantee (e.g. 95%).
  3. Abstention — objects whose conformal set is {CONFIRMED, FALSE POSITIVE}
     are ambiguous; the honest answer is "needs human review".

Run:  python -m exojury.calibrate
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from . import config, data
from .train_baseline import make_model

ALPHA = 0.05  # conformal miscoverage: 95% coverage target


def reliability_table(y_true, proba, n_bins: int = 10) -> pd.DataFrame:
    """Mean predicted vs observed frequency per probability bin."""
    bins = np.clip((proba * n_bins).astype(int), 0, n_bins - 1)
    rows = []
    for b in range(n_bins):
        m = bins == b
        if m.sum() == 0:
            continue
        rows.append({
            "bin": f"{b/n_bins:.1f}-{(b+1)/n_bins:.1f}",
            "n": int(m.sum()),
            "mean_predicted": float(proba[m].mean()),
            "observed_rate": float(y_true[m].mean()),
        })
    return pd.DataFrame(rows)


def expected_calibration_error(y_true, proba, n_bins: int = 10) -> float:
    tab = reliability_table(y_true, proba, n_bins)
    w = tab["n"] / tab["n"].sum()
    return float((w * (tab["mean_predicted"] - tab["observed_rate"]).abs()).sum())


def conformal_qhat(y_calib, proba_calib, alpha: float = ALPHA) -> float:
    """Split-conformal quantile of nonconformity scores (1 - p_true)."""
    scores = np.where(y_calib == 1, 1.0 - proba_calib, proba_calib)
    n = len(scores)
    q = np.ceil((n + 1) * (1 - alpha)) / n
    return float(np.quantile(scores, min(q, 1.0), method="higher"))


def conformal_sets(proba, qhat: float) -> pd.Series:
    """Prediction set per object: which labels are plausible at 1-alpha.

    An empty set (mid-range probability, typical of neither class) and a
    two-label set (qhat > 0.5, plausible as both) are both, operationally,
    an abstention: the pipeline hands the object to a human.
    """
    in_confirmed = (1.0 - proba) <= qhat
    in_fp = proba <= qhat
    labels = np.select(
        [in_confirmed & in_fp, in_confirmed, in_fp],
        ["NEEDS REVIEW (both plausible)", "CONFIRMED", "FALSE POSITIVE"],
        default="NEEDS REVIEW (ambiguous)",
    )
    return pd.Series(labels)


def main():
    df = data.load_raw()
    labeled, candidates = data.split_labeled_candidates(df)
    train_df, test_df = data.make_splits(labeled)

    # Carve a calibration slice out of the training data. The test set
    # stays untouched: it is only ever used for final evaluation.
    y_all = train_df[config.TARGET].map(config.LABEL_MAP_BINARY)
    fit_df, calib_df = train_test_split(
        train_df, test_size=0.25, stratify=y_all, random_state=config.SEED
    )

    def xy(d, leaky=False):
        return (
            data.build_features(d, include_vetting_flags=leaky),
            d[config.TARGET].map(config.LABEL_MAP_BINARY).values,
        )

    X_fit, y_fit = xy(fit_df)
    X_calib, y_calib = xy(calib_df)
    X_test, y_test = xy(test_df)

    # --- 1. calibration (isotonic on internal CV over the fit split) ---
    raw = make_model().fit(X_fit, y_fit)
    cal = CalibratedClassifierCV(make_model(), method="isotonic", cv=5)
    cal.fit(X_fit, y_fit)

    for name, mdl in [("uncalibrated", raw), ("isotonic", cal)]:
        p = mdl.predict_proba(X_test)[:, 1]
        print(
            f"{name:14s} test: AUC={roc_auc_score(y_test, p):.4f} "
            f"Brier={brier_score_loss(y_test, p):.4f} "
            f"ECE={expected_calibration_error(y_test, p):.4f}"
        )

    p_test = cal.predict_proba(X_test)[:, 1]
    print("\nReliability table (calibrated, test):")
    print(reliability_table(y_test, p_test).to_string(index=False))

    # --- 2. conformal on the held-aside calibration slice ---
    p_calib = cal.predict_proba(X_calib)[:, 1]
    qhat = conformal_qhat(y_calib, p_calib)
    sets_test = conformal_sets(p_test, qhat)
    covered = np.where(
        y_test == 1, sets_test.isin(["CONFIRMED", "NEEDS REVIEW (both plausible)"]),
        sets_test.isin(["FALSE POSITIVE", "NEEDS REVIEW (both plausible)"]),
    )
    print(f"\nConformal qhat={qhat:.4f} (alpha={ALPHA})")
    print(f"Empirical coverage on test: {covered.mean():.4f} (target {1-ALPHA:.2f})")
    print("\nPrediction-set breakdown on test:")
    print(sets_test.value_counts().to_string())

    # Decisiveness vs correctness among decisive predictions
    decisive = sets_test.isin(["CONFIRMED", "FALSE POSITIVE"]).values
    correct = (
        (sets_test.values == "CONFIRMED") & (y_test == 1)
        | (sets_test.values == "FALSE POSITIVE") & (y_test == 0)
    )
    print(f"\nDecisive on {decisive.mean()*100:.1f}% of test objects; "
          f"accuracy among decisive: {correct[decisive].mean()*100:.2f}%")

    # --- 3. score the real CANDIDATE frontier ---
    X_cand = data.build_features(candidates)[X_fit.columns]
    p_cand = cal.predict_proba(X_cand)[:, 1]
    sets_cand = conformal_sets(p_cand, qhat)
    out = candidates[["kepoi_name", "koi_period", "koi_prad", "koi_teq"]].copy()
    out["p_planet_calibrated"] = p_cand
    out["conformal_verdict"] = sets_cand.values
    out = out.sort_values("p_planet_calibrated", ascending=False)
    config.REPORTS_DIR.mkdir(exist_ok=True)
    out.to_csv(config.REPORTS_DIR / "candidate_scores.csv", index=False)
    print("\nCANDIDATE frontier verdicts:")
    print(sets_cand.value_counts().to_string())
    print(f"\nTop 10 most promising unconfirmed candidates:")
    print(out.head(10).to_string(index=False))

    config.MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(
        {"model": cal, "features": list(X_fit.columns), "qhat": qhat, "alpha": ALPHA},
        config.MODELS_DIR / "calibrated_conformal.joblib",
    )
    print(f"\nSaved calibrated model + conformal threshold to models/")


if __name__ == "__main__":
    main()
