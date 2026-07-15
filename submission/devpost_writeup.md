# Devpost submission — ExoJury

*(Paste sections into the Devpost form. Tagline first.)*

## Tagline (one line)

Every Kepler candidate gets a fair trial: a calibrated verdict, a 95%
statistical guarantee, and an AI-written opinion — from a pipeline that
found real errors in NASA's own catalog.

## Inspiration

When we plotted our first model's 99%+ accuracy, we got suspicious instead
of excited. Digging in, we found the dataset quietly contains the answer
key: columns like `koi_pdisposition` and the Robovetter `fpflag`s are
*outputs* of NASA's vetting, and two lines of code using them score 99.96%
with zero machine learning. Most models trained on this table are partly
grading themselves with the teacher's answer sheet. We decided our project
would be about **honesty**: what can you really tell about a distant signal
from the physics alone — and how sure are you allowed to be?

## What it does

ExoJury puts all 9,564 Kepler Objects of Interest on trial:

1. **Honest classifier** — gradient boosting on transit and stellar
   observables only, under a documented per-column leakage policy. 98.2%
   held-out accuracy, ROC-AUC 0.997 — and we quantify exactly how many
   points the leaky columns would have inflated (+1.3).
2. **Calibrated probabilities** — isotonic calibration (ECE 0.009), so
   "90%" means 90%.
3. **Conformal prediction** — every object gets a prediction set with a
   finite-sample 95% coverage guarantee (empirical 95.6%). When the
   evidence is ambiguous, ExoJury says **NEEDS REVIEW** instead of
   guessing — on the unresolved candidates it abstains 3× more often than
   on labeled data, correctly sensing they're harder.
4. **Label audit** — confident learning flags catalog labels the model
   most disagrees with. Its #1 flag, "confirmed planet" Kepler-854 b
   (p_planet = 0.00003), was *actually demoted to false positive by NASA*
   (Niraula et al. 2022) — our snapshot predates the fix. Same for
   Kepler-840 b. It also flagged Kepler-452 b, whose validation is
   formally disputed in the literature. The pipeline rediscovered real
   catalog errors from this CSV alone.
5. **Follow-up ranking** — the 1,978 unresolved CANDIDATEs scored and
   sorted: 335 planet-like with a 95% guarantee, 1,125 false-positive-like,
   518 flagged for human eyes. A telescope-time priority list.
6. **AI vetting dossiers** — DeepSeek-V3 via Featherless.ai writes an
   astronomer-style SIGNAL / ASSESSMENT / FOLLOW-UP report for any object,
   grounded strictly in numbers the pipeline computed. The model decides;
   the LLM narrates.
7. **Mission control** — a Streamlit app to try any KOI live.

## How we built it

Python + scikit-learn (HistGradientBoosting — handles missing values
natively), a hand-rolled split conformal implementation (~30 lines, no
library magic), cleanlab for the label audit, matplotlib for figures,
Streamlit for the app, and the sponsor's Featherless API (OpenAI-compatible)
for dossiers. Physics-motivated feature engineering: transit duty cycle,
depth-vs-radius-ratio consistency, centroid offset significance (background
eclipsing binary signature), SNR per transit.

## Challenges we ran into

- **Leakage is sneaky.** `kepler_name` looks like an innocent string column;
  it's a perfect label. We ended up assigning all 140 columns to explicit
  tiers and testing the "answer key" accuracy directly.
- **Calibration on imbalanced, near-separable data** — mid-probability bins
  hold very few objects, so we had to read reliability diagrams carefully
  (marker size = bin population) instead of trusting wiggly lines.
- **The CANDIDATE class.** Treating it as a third class caps you at ~86%
  accuracy because it's not a kind of object, it's a state of knowledge. We
  report the 3-class metrics the challenge asks for, then argue the better
  framing: binary training + scoring candidates as unlabeled objects.

## Accomplishments we're proud of

The audit table. A student-scale pipeline, given one CSV, independently
flagged planets that NASA later demoted — before we ever searched the
literature. Also: a conformal guarantee that actually holds (95.6% vs 95%
target) on real astronomical data.

## What we learned

Accuracy is the least interesting number in a scientific ML project. The
interesting ones are: how much of your accuracy is leakage, whether your
probabilities mean anything, and whether your model knows when it doesn't
know.

## What's next

Cross-matching our 335 guaranteed planet-like candidates against TESS and
Gaia DR3 to see which have since been confirmed — turning the priority list
into testable predictions.

## Built with

`python` `scikit-learn` `cleanlab` `streamlit` `matplotlib` `featherless.ai`
`deepseek-v3` `conformal-prediction` `nasa-exoplanet-archive`
