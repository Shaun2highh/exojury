"""Baseline: honest model vs leaky model vs the no-ML answer key.

Run:  python -m exojury.train_baseline
"""

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from . import config, data


def answer_key_accuracy(df) -> float:
    """No ML: reconstruct the label from leakage columns alone."""
    pred = np.where(
        df["kepler_name"].notna(),
        "CONFIRMED",
        np.where(
            df["koi_pdisposition"] == "FALSE POSITIVE", "FALSE POSITIVE", "CANDIDATE"
        ),
    )
    return accuracy_score(df[config.TARGET], pred)


def make_model() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=250,
        learning_rate=0.08,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=25,
        random_state=config.SEED,
    )


def evaluate(name: str, y_true, proba) -> dict:
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "roc_auc": roc_auc_score(y_true, proba),
        "pr_auc": average_precision_score(y_true, proba),
        "f1": f1_score(y_true, pred),
        "accuracy": accuracy_score(y_true, pred),
        "brier": brier_score_loss(y_true, proba),
    }
    row = "  ".join(f"{k}={v:.4f}" for k, v in metrics.items())
    print(f"{name:28s} {row}")
    return metrics


def main():
    df = data.load_raw()
    labeled, candidates = data.split_labeled_candidates(df)
    print(f"Labeled rows: {len(labeled)}  (CONFIRMED vs FALSE POSITIVE)")
    print(f"Candidate rows held aside for scoring: {len(candidates)}\n")

    print(f"Answer-key columns, zero ML -> accuracy {answer_key_accuracy(df):.4f} "
          f"(this is why leakage control matters)\n")

    train_df, test_df = data.make_splits(labeled)
    y_train = train_df[config.TARGET].map(config.LABEL_MAP_BINARY).values
    y_test = test_df[config.TARGET].map(config.LABEL_MAP_BINARY).values

    results = {}
    for label, leaky in [("HONEST (no vetting flags)", False), ("LEAKY (with fpflags)", True)]:
        X_train = data.build_features(train_df, include_vetting_flags=leaky)
        X_test = data.build_features(test_df, include_vetting_flags=leaky)

        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.SEED)
        cv_proba = cross_val_predict(
            make_model(), X_train, y_train, cv=cv, method="predict_proba"
        )[:, 1]
        print(f"\n--- {label} ({X_train.shape[1]} features) ---")
        evaluate("5-fold CV (train)", y_train, cv_proba)

        model = make_model().fit(X_train, y_train)
        test_metrics = evaluate("Held-out test", y_test, model.predict_proba(X_test)[:, 1])
        results[label] = test_metrics

        if not leaky:
            pi = permutation_importance(
                model, X_test, y_test, n_repeats=3, random_state=config.SEED,
                scoring="roc_auc",
            )
            imp = sorted(
                zip(X_test.columns, pi.importances_mean), key=lambda t: -t[1]
            )[:15]
            print("\nTop 15 features by permutation importance (honest model):")
            for c, v in imp:
                print(f"  {c:28s} {v:.4f}")
            config.MODELS_DIR.mkdir(exist_ok=True)
            joblib.dump(
                {"model": model, "features": list(X_train.columns)},
                config.MODELS_DIR / "baseline_honest.joblib",
            )
            train_df.to_csv(config.MODELS_DIR / "train_split.csv", index=False)
            test_df.to_csv(config.MODELS_DIR / "test_split.csv", index=False)

    gap = results["LEAKY (with fpflags)"]["accuracy"] - results["HONEST (no vetting flags)"]["accuracy"]
    print(f"\nAccuracy inflation from vetting-flag leakage: +{gap*100:.1f} points")


if __name__ == "__main__":
    main()
