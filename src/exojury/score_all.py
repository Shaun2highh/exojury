"""Precompute calibrated scores + conformal verdicts for every KOI.

Writes reports/scores_all.csv consumed by the dashboard, so the app never
runs the model at page-load time.

Run:  python -m exojury.score_all
"""

import joblib
import numpy as np
import pandas as pd

from . import config, data
from .calibrate import conformal_sets


def main():
    bundle = joblib.load(config.MODELS_DIR / "calibrated_conformal.joblib")
    test_names = set(
        pd.read_csv(config.MODELS_DIR / "test_split.csv")["kepoi_name"]
    )
    df = data.load_raw()
    X = data.build_features(df)[bundle["features"]]
    p = bundle["model"].predict_proba(X)[:, 1]
    verdict = conformal_sets(p, bundle["qhat"]).values

    feats = data.engineer_features(df)
    out = pd.DataFrame({
        "kepoi_name": df["kepoi_name"],
        "kepler_name": df["kepler_name"],
        "catalog": df[config.TARGET],
        "p_planet": p,
        "verdict": verdict,
        # objects the model trained on vs never saw (test/candidates)
        "unseen": df["kepoi_name"].isin(test_names)
        | (df[config.TARGET] == "CANDIDATE"),
        "ra": df["ra"], "dec": df["dec"],
        "koi_period": df["koi_period"],
        "koi_prad": df["koi_prad"],
        "koi_teq": df["koi_teq"],
        "koi_depth": df["koi_depth"],
        "koi_duration": df["koi_duration"],
        "koi_model_snr": df["koi_model_snr"],
        "koi_insol": df["koi_insol"],
        "koi_impact": df["koi_impact"],
        "koi_count": df["koi_count"],
        "koi_steff": df["koi_steff"],
        "koi_srad": df["koi_srad"],
        "koi_kepmag": df["koi_kepmag"],
        "duty_cycle": feats["duty_cycle"],
        "dicco_offset_sig": feats["dicco_offset_sig"],
        "prad_over_srad": feats["prad_over_srad"],
    })
    config.REPORTS_DIR.mkdir(exist_ok=True)
    out.to_csv(config.REPORTS_DIR / "scores_all.csv", index=False)
    print(f"scored {len(out)} KOIs -> reports/scores_all.csv")
    print(out.groupby("catalog")["verdict"].value_counts().to_string())


if __name__ == "__main__":
    main()
