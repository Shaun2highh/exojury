"""Assemble the narrative notebook from saved artifacts.

Run:  python -m exojury.build_notebook
Then: jupyter nbconvert --to notebook --execute notebooks/ExoJury_report.ipynb
"""

import nbformat as nbf

from . import config

nb = nbf.v4.new_notebook()
md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

C = []

C.append(md("""# ExoJury 🪐⚖️ — every Kepler candidate gets a fair trial

**India High School Exoplanet Data Challenge (Celesta)**

This notebook walks through the whole project on the NASA KOI cumulative
table: the leakage audit, the honest model, calibration, conformal
prediction, the label audit that found real catalog errors, and the ranked
candidate frontier. It runs from saved pipeline artifacts in seconds; to
retrain from scratch, see the README.
"""))

C.append(code("""import sys, joblib
import numpy as np, pandas as pd
sys.path.insert(0, "../src")
from exojury import config, data
from exojury.calibrate import conformal_sets, reliability_table, expected_calibration_error

df = data.load_raw()
print(df.shape)
df["koi_disposition"].value_counts()"""))

C.append(md("""## 1. The dataset contains the answer key

Before modeling, we checked every one of the 140 columns for **leakage** —
columns that are *outputs* of NASA's vetting process rather than
observations. Four kinds hide here: `kepler_name` (only confirmed planets
get names), `koi_pdisposition` (the pipeline's own verdict),
`koi_comment` (the vetting rationale in text), and the Robovetter
`koi_fpflag_*` flags."""))

C.append(code("""# The "answer key" classifier: two lines, zero ML
pred = np.where(df["kepler_name"].notna(), "CONFIRMED",
        np.where(df["koi_pdisposition"] == "FALSE POSITIVE", "FALSE POSITIVE", "CANDIDATE"))
print(f"Answer-key accuracy: {(pred == df['koi_disposition']).mean():.4f}")

anyflag = df[config.VETTING_FLAG_COLS].sum(axis=1) > 0
lab = df[df["koi_disposition"] != "CANDIDATE"]
pred2 = np.where(anyflag[lab.index], "FALSE POSITIVE", "CONFIRMED")
print(f"fpflags-only accuracy (binary): {(pred2 == lab['koi_disposition']).mean():.4f}")"""))

C.append(md("""Any model trained with these columns is partly copying the
teacher's answer sheet. Our leakage policy (`src/exojury/config.py`)
excludes them all. **Everything below uses physics only.**

![leakage](../reports/figures/04_leakage_answer_key.png)

## 2. Exploration

![classes](../reports/figures/01_class_balance.png)
![period-radius](../reports/figures/02_period_radius.png)

False positives dominate the "giant planet" regime — objects with fitted
radii above ~2 Jupiter radii are almost always eclipsing binary stars, not
planets. Feature separations follow known astrophysics (centroid offsets ⇒
background binaries; odd-even depth differences ⇒ eclipsing binaries):

![separation](../reports/figures/03_feature_separation.png)

## 3. The honest model

Binary task: CONFIRMED vs FALSE POSITIVE (the CANDIDATE rows are *unlabeled
by definition* — we score them in §6 instead of pretending they're a
class). Gradient boosting (`HistGradientBoostingClassifier`), stratified
80/20 split, 105 physics features, NaNs handled natively."""))

C.append(code("""raw = joblib.load(config.MODELS_DIR / "baseline_honest.joblib")
test_df = pd.read_csv(config.MODELS_DIR / "test_split.csv")
y_test = test_df["koi_disposition"].map(config.LABEL_MAP_BINARY).values
X_test = data.build_features(test_df)[raw["features"]]

from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
p = raw["model"].predict_proba(X_test)[:, 1]
print(f"Held-out test: ROC-AUC={roc_auc_score(y_test, p):.4f}  "
      f"acc={accuracy_score(y_test, p >= .5):.4f}  f1={f1_score(y_test, p >= .5):.4f}")"""))

C.append(md("""Including the Robovetter flags would add +1.3 accuracy
points — inflation we *measured* rather than shipped (see README table).
For the challenge's 3-class formulation we get 86.1% accuracy / 0.831
macro-F1 (`python -m exojury.three_class`); CANDIDATE is the weak class
(F1 0.68) precisely because it's a state of knowledge, not a kind of object.

![confusion](../reports/figures/05_confusion_3class.png)

## 4. Honest uncertainty: calibration + a 95% guarantee

A probability is only useful if it's *calibrated* — "90%" should come true
~90% of the time. We use isotonic calibration, then **split conformal
prediction** on a held-aside calibration slice: every object gets a
prediction *set* guaranteed to contain the truth 95% of the time. An empty
set means "typical of neither class" → **NEEDS REVIEW**."""))

C.append(code("""cal = joblib.load(config.MODELS_DIR / "calibrated_conformal.joblib")
p_cal = cal["model"].predict_proba(data.build_features(test_df)[cal["features"]])[:, 1]
print(f"ECE after calibration: {expected_calibration_error(y_test, p_cal):.4f}")
sets_test = conformal_sets(p_cal, cal["qhat"])
covered = np.where(y_test == 1,
                   sets_test.isin(["CONFIRMED", "NEEDS REVIEW (both plausible)"]),
                   sets_test.isin(["FALSE POSITIVE", "NEEDS REVIEW (both plausible)"]))
print(f"Empirical coverage: {covered.mean():.4f} (target 0.95, qhat={cal['qhat']:.3f})")
sets_test.value_counts()"""))

C.append(md("""![reliability](../reports/figures/06_reliability.png)
![conformal](../reports/figures/07_conformal_verdicts.png)

## 5. Auditing NASA's own labels 🏆

Confident learning (cleanlab) asks: which catalog labels does an
out-of-fold model most confidently disagree with? We checked the top flags
against the literature **after** the model produced them:

| KOI | Catalog (our snapshot) | Model p(planet) | Literature |
|---|---|---|---|
| K01450.01 (Kepler-854 b) | CONFIRMED | 0.00003 | **Demoted to false positive** (Niraula et al. 2022) |
| K01416.01 (Kepler-840 b) | CONFIRMED | 0.0016 | **Demoted to false positive** (same study) |
| K07016.01 (Kepler-452 b) | CONFIRMED | 0.0006 | Validation formally disputed (Mullally et al. 2018) |
| K03794.01 (Kepler-1520 b) | CONFIRMED | 0.003 | Real, but *disintegrating* — an honest miss |

The pipeline rediscovered real catalog corrections from this CSV alone."""))

C.append(code("""audit = pd.read_csv(config.REPORTS_DIR / "label_audit.csv")
audit.head(10)"""))

C.append(md("""## 6. The frontier: 1,978 unresolved candidates, ranked

Trained on labeled rows only, ExoJury scores every CANDIDATE with a
calibrated probability and conformal verdict — a telescope-time priority
list. 74% get a 95%-guaranteed verdict; the rest are honestly flagged for
human review."""))

C.append(code("""scores = pd.read_csv(config.REPORTS_DIR / "candidate_scores.csv")
print(scores["conformal_verdict"].value_counts().to_string(), "\\n")
scores.head(10)"""))

C.append(md("""## 7. AI vetting dossiers (Featherless.ai)

For any KOI, DeepSeek-V3 (via the sponsor's OpenAI-compatible API) writes
an astronomer-style report grounded strictly in the pipeline's numbers.
**The sklearn model decides; the LLM narrates.** Example — the dossier for
audit hit #1, Kepler-854 b:"""))

C.append(code("""from IPython.display import Markdown
dossier = (config.REPORTS_DIR / "dossiers" / "K01450.01.md")
Markdown(dossier.read_text() if dossier.exists()
         else "_Run `python -m exojury.dossier --batch` (needs FEATHERLESS_API_KEY)_")"""))

C.append(md("""## Conclusions

- **Accuracy is the least interesting number.** What matters: how much of
  it is leakage (+1.3 pts here), whether probabilities are calibrated
  (ECE 0.009), and whether the model knows when it doesn't know (26%
  abstention on the genuinely-hard frontier vs 3% on labeled data).
- Built to **distrust labels**, the pipeline found real catalog errors that
  NASA corrected years after this snapshot.
- Everything is reproducible: `README.md` has the exact commands; every
  random seed is fixed.

*Data: NASA Exoplanet Archive KOI cumulative table (DOI 10.26133/NEA4),
NASA Exoplanet Science Institute at IPAC/Caltech. Challenge: Celesta.*"""))

nb["cells"] = C
out = config.PROJECT_ROOT / "notebooks" / "ExoJury_report.ipynb"
out.parent.mkdir(exist_ok=True)
nbf.write(nb, out)
print(f"wrote {out}")
