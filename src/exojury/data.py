"""Loading, cleaning, feature engineering, and splitting for the KOI table."""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from . import config


def load_raw() -> pd.DataFrame:
    return pd.read_csv(config.DATA_RAW)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add physics-motivated derived features. All inputs are transit-fit
    observables, never vetting outputs."""
    out = df.copy()

    # How many of the 17 Kepler quarters observed this target.
    if "koi_quarters" in out.columns:
        out["n_quarters"] = (
            out["koi_quarters"].astype(str).str.count("1").where(out["koi_quarters"].notna())
        )

    # Fraction of the orbit spent in transit. Eclipsing binaries and
    # blended signals often show implausible duty cycles.
    out["duty_cycle"] = out["koi_duration"] / (out["koi_period"] * 24.0)

    # Consistency between measured depth and depth implied by the fitted
    # radius ratio (depth ~ ror^2). Large disagreement flags bad fits.
    implied_depth_ppm = (out["koi_ror"] ** 2) * 1e6
    out["depth_vs_ror"] = np.log1p(out["koi_depth"]) - np.log1p(implied_depth_ppm)

    # Detection strength normalised per transit.
    out["snr_per_transit"] = out["koi_model_snr"] / np.sqrt(
        out["koi_num_transits"].clip(lower=1)
    )

    # Centroid-offset significance: how many sigma the transit source is
    # displaced from the target star (background eclipsing-binary signature).
    for src in ("dicco", "dikco"):
        col, err = f"koi_{src}_msky", f"koi_{src}_msky_err"
        out[f"{src}_offset_sig"] = out[col] / out[err].replace(0, np.nan)

    # Planet radius relative to its star (sanity: "planets" bigger than
    # ~0.2 R_star are usually stellar companions).
    out["prad_over_srad"] = out["koi_prad"] / (out["koi_srad"] * 109.1)

    return out


def build_features(
    df: pd.DataFrame, include_vetting_flags: bool = False
) -> pd.DataFrame:
    """Return the model feature matrix under the leakage policy.

    include_vetting_flags=True reproduces what most naive models do
    (training on Robovetter outputs) — used only to quantify the inflation.
    """
    df = engineer_features(df)
    drop = set(config.DROP_ALWAYS) | {config.TARGET}
    if not include_vetting_flags:
        drop |= set(config.VETTING_FLAG_COLS)
    keep = [c for c in df.columns if c not in drop]
    X = df[keep]
    non_numeric = X.select_dtypes(exclude="number").columns.tolist()
    if non_numeric:
        raise ValueError(f"Non-numeric feature columns slipped through: {non_numeric}")
    return X


def split_labeled_candidates(df: pd.DataFrame):
    """CONFIRMED/FALSE POSITIVE rows are our labeled data; CANDIDATE rows
    are the unlabeled frontier we ultimately score."""
    labeled = df[df[config.TARGET].isin(["CONFIRMED", "FALSE POSITIVE"])].copy()
    candidates = df[df[config.TARGET] == "CANDIDATE"].copy()
    return labeled, candidates


def make_splits(labeled: pd.DataFrame, test_size: float = 0.2, seed: int = config.SEED):
    """Stratified train/test split on the labeled rows."""
    y = labeled[config.TARGET].map(config.LABEL_MAP_BINARY)
    train_df, test_df = train_test_split(
        labeled, test_size=test_size, stratify=y, random_state=seed
    )
    return train_df, test_df
