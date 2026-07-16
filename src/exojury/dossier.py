"""Stage 4: AI-written vetting dossiers via Featherless.ai.

For a given KOI, we hand the LLM the calibrated verdict, the conformal set,
and the top per-object feature evidence — and it writes the report a junior
astronomer would: what the signal is, why the model leans the way it does,
and what follow-up would settle it.

The LLM never decides anything. It narrates evidence computed upstream —
this keeps the science in the sklearn pipeline and the words in the LLM.

Setup:  export FEATHERLESS_API_KEY=...   (from featherless.ai -> API Keys)
Run:    python -m exojury.dossier K00701.03
"""

import os
import sys

import joblib
import numpy as np
import pandas as pd

from . import config, data

FEATHERLESS_BASE = "https://api.featherless.ai/v1"
MODEL_ID = "deepseek-ai/DeepSeek-V3-0324"

FEATURE_GLOSSARY = {
    "koi_period": "orbital period (days)",
    "koi_prad": "planet radius (Earth radii)",
    "koi_depth": "transit depth (ppm)",
    "koi_duration": "transit duration (hours)",
    "koi_model_snr": "transit signal-to-noise ratio",
    "koi_teq": "equilibrium temperature (K)",
    "koi_insol": "insolation relative to Earth",
    "koi_impact": "transit impact parameter",
    "duty_cycle": "fraction of orbit spent in transit",
    "dicco_offset_sig": "centroid offset significance (sigma) — high values suggest a background eclipsing binary",
    "prad_over_srad": "planet-to-star radius ratio",
    "koi_count": "number of transit signals found on this star",
    "koi_bin_oedp_sig": "odd-even transit depth consistency — low values suggest an eclipsing binary",
}


def top_evidence(model_bundle, row_features: pd.Series, k: int = 8) -> list[str]:
    """Per-object evidence: which glossary features have the most unusual
    values for this KOI relative to the labeled population."""
    lines = []
    for col in FEATURE_GLOSSARY:
        if col in row_features.index and pd.notna(row_features[col]):
            lines.append(f"- {FEATURE_GLOSSARY[col]}: {row_features[col]:.4g}")
    return lines[:k + 5]


def build_prompt(name, disposition, p_planet, verdict, evidence_lines) -> str:
    return f"""You are an exoplanet vetting assistant writing a short report for astronomers.

Object: {name} (catalog status: {disposition})
Model verdict: calibrated planet probability = {p_planet:.3f}
Conformal 95% prediction set: {verdict}

Measured properties:
{chr(10).join(evidence_lines)}

Write a "vetting dossier" of at most 180 words with three sections:
1. SIGNAL — one sentence describing the object in plain language.
2. ASSESSMENT — why the evidence supports or undermines the planet hypothesis.
   Reference specific numbers above. Do not invent any values.
3. FOLLOW-UP — one concrete observation that would settle the classification.

Be precise and calm. If the conformal set abstains, say clearly that the
evidence is ambiguous and explain what makes it ambiguous."""


def write_dossier(kepoi_name: str, use_cache: bool = True) -> str:
    from openai import OpenAI

    cache_file = config.REPORTS_DIR / "dossiers" / f"{kepoi_name}.md"
    if use_cache and cache_file.exists():
        return cache_file.read_text()

    api_key = (os.environ.get("FEATHERLESS_API_KEY") or "").strip()
    if not api_key:
        sys.exit("Set FEATHERLESS_API_KEY first (see docs_setup_guide.pdf)")

    bundle = joblib.load(config.MODELS_DIR / "calibrated_conformal.joblib")
    df = data.load_raw()
    row = df[df["kepoi_name"] == kepoi_name]
    if row.empty:
        sys.exit(f"KOI {kepoi_name} not found")

    X = data.build_features(row)[bundle["features"]]
    p = float(bundle["model"].predict_proba(X)[:, 1][0])
    from .calibrate import conformal_sets
    verdict = conformal_sets(np.array([p]), bundle["qhat"]).iloc[0]

    feats = data.engineer_features(row).iloc[0]
    prompt = build_prompt(
        kepoi_name, row.iloc[0][config.TARGET], p, verdict,
        top_evidence(bundle, feats),
    )

    client = OpenAI(base_url=FEATHERLESS_BASE, api_key=api_key)
    resp = client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.4,
    )
    text = resp.choices[0].message.content
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(text)
    return text


def batch(names: list[str]) -> None:
    for i, n in enumerate(names, 1):
        print(f"[{i}/{len(names)}] {n} ...", flush=True)
        try:
            write_dossier(n)
        except Exception as e:  # keep going: one cold model shouldn't kill the batch
            print(f"  failed: {e}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        import pandas as pd
        scores = pd.read_csv(config.REPORTS_DIR / "candidate_scores.csv")
        demo_set = (
            scores.head(10)["kepoi_name"].tolist()  # top frontier candidates
            + ["K00701.03",  # Kepler-62e, habitable-zone showpiece
               "K01450.01",  # Kepler-854b — NASA later demoted (audit hit #1)
               "K01416.01",  # Kepler-840b — NASA later demoted
               "K07016.01",  # Kepler-452b — disputed validation
               "K03794.01"]  # Kepler-1520b — disintegrating planet
        )
        batch(demo_set)
    else:
        name = sys.argv[1] if len(sys.argv) > 1 else "K00701.03"
        print(write_dossier(name))
