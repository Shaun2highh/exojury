"""ExoJury mission control.  Run:  streamlit run app/dashboard.py"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exojury import config, data  # noqa: E402
from exojury.calibrate import conformal_sets  # noqa: E402

st.set_page_config(page_title="ExoJury", page_icon="🪐", layout="wide")

CLASS_COLORS = {
    "CONFIRMED": "#2a78d6",
    "CANDIDATE": "#eda100",
    "FALSE POSITIVE": "#e34948",
}


@st.cache_resource
def load_artifacts():
    bundle = joblib.load(config.MODELS_DIR / "calibrated_conformal.joblib")
    df = data.load_raw()
    scores = pd.read_csv(config.REPORTS_DIR / "candidate_scores.csv")
    audit_path = config.REPORTS_DIR / "label_audit.csv"
    audit = pd.read_csv(audit_path) if audit_path.exists() else None
    return bundle, df, scores, audit


try:
    bundle, df, scores, audit = load_artifacts()
except FileNotFoundError as e:
    st.error(f"Run the pipeline first (see README). Missing: {e.filename}")
    st.stop()

st.title("🪐⚖️ ExoJury")
st.caption(
    "Every Kepler candidate gets a fair trial: a calibrated verdict, "
    "a 95% statistical guarantee, and a written opinion."
)

tab_verdict, tab_frontier, tab_audit = st.tabs(
    ["🔭 Try a KOI", "🚀 Candidate frontier", "🧾 Label audit"]
)

with tab_verdict:
    col1, col2 = st.columns([1, 2])
    with col1:
        name = st.selectbox("Pick a KOI", df["kepoi_name"].tolist(),
                            index=int(np.where(df["kepoi_name"] == "K00701.03")[0][0]))
        row = df[df["kepoi_name"] == name]
        X = data.build_features(row)[bundle["features"]]
        p = float(bundle["model"].predict_proba(X)[:, 1][0])
        verdict = conformal_sets(np.array([p]), bundle["qhat"]).iloc[0]

        p_label = ">99.9%" if p > 0.999 else ("<0.1%" if p < 0.001 else f"{p*100:.1f}%")
        st.metric("Calibrated planet probability", p_label)
        st.metric("Conformal 95% verdict", verdict)
        st.metric("Catalog says", row.iloc[0][config.TARGET])

    with col2:
        st.subheader("Evidence")
        feats = data.engineer_features(row).iloc[0]
        show = {
            "Orbital period [days]": feats.get("koi_period"),
            "Planet radius [R⊕]": feats.get("koi_prad"),
            "Transit depth [ppm]": feats.get("koi_depth"),
            "Signal-to-noise": feats.get("koi_model_snr"),
            "Equilibrium temp [K]": feats.get("koi_teq"),
            "Centroid offset [σ]": feats.get("dicco_offset_sig"),
            "Duty cycle": feats.get("duty_cycle"),
            "Signals on this star": feats.get("koi_count"),
        }
        st.dataframe(
            pd.DataFrame(
                {"value": [f"{v:.4g}" if pd.notna(v) else "—" for v in show.values()]},
                index=show.keys(),
            ),
            width="stretch",
        )
        import os
        if os.environ.get("FEATHERLESS_API_KEY"):
            if st.button("✍️ Write AI vetting dossier"):
                from exojury.dossier import write_dossier
                with st.spinner("The clerk is writing..."):
                    st.markdown(write_dossier(name))
        else:
            st.info("Set FEATHERLESS_API_KEY to enable AI vetting dossiers.")

with tab_frontier:
    st.subheader("The 1,978 unresolved CANDIDATEs, ranked for follow-up")
    min_p = st.slider("Minimum calibrated planet probability", 0.0, 1.0, 0.8)
    view = scores[scores["p_planet_calibrated"] >= min_p]
    st.write(f"{len(view)} candidates above threshold")
    st.dataframe(view, width="stretch", height=420)
    st.download_button("Download ranked list (CSV)",
                       view.to_csv(index=False), "exojury_frontier.csv")

with tab_audit:
    st.subheader("KOIs where the model confidently disagrees with the catalog")
    if audit is None:
        st.info("Run `python -m exojury.audit` to generate the label audit.")
    else:
        st.dataframe(audit.head(50), width="stretch", height=480)
