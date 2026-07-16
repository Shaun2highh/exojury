"""Methods: honesty results, pipeline, glossary, limitations."""

import streamlit as st

from common import section
import ui


def page():
    section("Honesty", "Why our accuracy is lower than theirs — on purpose",
            "The KOI table contains NASA's own vetting outputs. kepler_name "
            "+ koi_pdisposition reconstruct the answer with 99.96% accuracy "
            "and zero ML; the Robovetter fpflag columns alone give 98.5%. "
            "ExoJury excludes every such column and measures the inflation "
            "instead of shipping it: +1.3 accuracy points.")

    st.markdown(ui.stat_row([
        ("0.9967", "ROC-AUC (honest, held-out)"),
        ("0.009", "expected calibration error"),
        ("95.6%", "conformal coverage (target 95%)"),
        ("+1.3 pts", "accuracy inflation from leakage"),
        ("86.1%", "3-class accuracy (challenge format)"),
    ]), unsafe_allow_html=True)

    a, b = st.columns(2, gap="large")
    with a:
        st.image("reports/figures/dark/04_leakage_answer_key.png",
                 caption="The answer key hiding in the dataset")
        st.image("reports/figures/dark/06_reliability.png",
                 caption="Calibration: when ExoJury says 90%, it happens "
                         "~90% of the time (ECE 0.009)")
    with b:
        st.image("reports/figures/dark/07_conformal_verdicts.png",
                 caption="Conformal coverage holds: 95.6% vs 95% target. On "
                         "the unresolved frontier the model abstains 3× more "
                         "often — it knows those are harder.")
        st.image("reports/figures/dark/05_confusion_3class.png",
                 caption="Challenge-required 3-class model (86.1%). "
                         "CANDIDATE is the weak class because it's a state "
                         "of knowledge, not a kind of object.")

    section("Methods", "The pipeline, start to finish")
    steps = [
        ("1 · Leakage audit", "All 140 columns assigned to documented "
         "tiers; everything the vetting process wrote is excluded."),
        ("2 · Honest model", "Gradient boosting on 105 physics features, "
         "with engineered features like duty cycle and depth-vs-radius "
         "consistency. 98.2% held-out accuracy."),
        ("3 · Calibration", "Isotonic regression so probabilities mean "
         "what they say (ECE 0.009)."),
        ("4 · Conformal guarantee", "Split conformal prediction: 95% "
         "coverage, abstains when the evidence is ambiguous."),
        ("5 · Label audit", "cleanlab confident learning found two planets "
         "NASA later demoted — from this CSV alone."),
        ("6 · The frontier", "All 1,978 unresolved candidates scored and "
         "ranked for follow-up."),
        ("7 · AI dossiers", "DeepSeek-V3 via Featherless narrates each "
         "verdict; the model decides, the LLM only writes."),
        ("8 · This app", "Streamlit + Plotly + three.js (vendored, works "
         "offline). Everything regenerates from README commands; all "
         "seeds fixed."),
    ]
    cols = st.columns(2, gap="medium")
    for i, (title, body) in enumerate(steps):
        with cols[i % 2]:
            st.markdown(f'<div class="card" style="margin-bottom:12px;">'
                        f'<h4>{title}</h4><p>{body}</p></div>',
                        unsafe_allow_html=True)

    section("Glossary", "The words on this dashboard")
    GLOSSARY = {
        "KOI": "Kepler Object of Interest — a periodic dimming signal that "
               "might be a planet crossing its star.",
        "Transit depth (ppm)": "How much starlight the object blocks. "
               "Earth crossing the Sun: ~84 ppm.",
        "Impact parameter": "How centrally the object crosses the star; "
               ">1 means it barely grazes — a binary-star signature.",
        "Centroid offset σ": "How far the light's centre shifts during "
               "transit. Big shifts mean the dimming comes from a "
               "background star.",
        "Odd–even test": "Eclipsing binaries alternate deep/shallow "
               "events; planets don't.",
        "Duty cycle": "Fraction of the orbit spent in transit.",
        "Calibrated probability": "Of all objects given 90%, ~90% really "
               "are planets.",
        "Conformal prediction": "A distribution-free wrapper giving "
               "prediction sets with a finite-sample coverage guarantee — "
               "the 95% is math, not vibes.",
        "NEEDS REVIEW": "When neither label fits at 95% confidence, the "
               "pipeline hands the object to a human instead of guessing.",
        "Confident learning": "Using out-of-fold predictions to find "
               "training labels that are probably wrong.",
        "Leakage": "Any feature computed from the answer. Models trained "
               "on it are partly grading themselves with the answer key.",
    }
    g1, g2 = st.columns(2, gap="medium")
    items = list(GLOSSARY.items())
    for i, (term, defn) in enumerate(items):
        with (g1 if i < (len(items) + 1) // 2 else g2):
            st.markdown(f"**{term}** — {defn}")

    section("Fine print", "Data & honest limitations")
    st.markdown(
        "- **Data**: NASA Exoplanet Archive, KOI cumulative table "
        "(DOI 10.26133/NEA4), provided by the Celesta challenge. Data by "
        "the NASA Exoplanet Science Institute at IPAC/Caltech.\n"
        "- **Reproducibility**: every figure and number regenerates from "
        "the commands in `README.md`; all random seeds fixed.\n"
        "- **Limitations**: the model sees fitted parameters, not raw "
        "light curves; the catalog snapshot predates post-2018 revisions "
        "(which is exactly how the audit could be verified); the "
        "habitable-zone tag is a coarse T_eq heuristic; a few features may "
        "partly encode observation effort rather than physics.")
