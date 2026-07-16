"""ExoJury mission control.  Run:  streamlit run app/dashboard.py"""

import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exojury import config, data  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui  # noqa: E402

st.set_page_config(page_title="ExoJury", page_icon="🪐", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(ui.CSS, unsafe_allow_html=True)

PANEL = "#111318"
INK = "#ffffff"
INK2 = "#c3c2b7"
MUTED = "#898781"
GRID = "#262a31"
BLUE, YELLOW, RED, VIOLET = ui.BLUE, ui.YELLOW, ui.RED, ui.VIOLET

VERDICT_STYLE = {
    "CONFIRMED": (BLUE, "🪐", "PLANET"),
    "FALSE POSITIVE": (RED, "✖", "FALSE POSITIVE"),
    "NEEDS REVIEW (ambiguous)": (YELLOW, "🔍", "NEEDS REVIEW"),
    "NEEDS REVIEW (both plausible)": (YELLOW, "🔍", "NEEDS REVIEW"),
}
CATALOG_COLOR = {"CONFIRMED": BLUE, "CANDIDATE": YELLOW, "FALSE POSITIVE": RED}


def rgba(hex_color: str, a: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{a})"


PLOTLY_LAYOUT = dict(
    paper_bgcolor=PANEL, plot_bgcolor=PANEL,
    font=dict(color=INK2, family="Space Grotesk, system-ui, sans-serif", size=12),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#383835"),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#383835"),
    margin=dict(l=10, r=10, t=34, b=10),
)


@st.cache_resource
def load_artifacts():
    bundle = joblib.load(config.MODELS_DIR / "calibrated_conformal.joblib")
    scores = pd.read_csv(config.REPORTS_DIR / "scores_all.csv")
    audit = pd.read_csv(config.REPORTS_DIR / "label_audit.csv")
    return bundle, scores, audit


@st.cache_data
def class_percentiles(feature: str):
    s = SCORES
    pl = np.sort(s.loc[s.catalog == "CONFIRMED", feature].dropna().values)
    fp = np.sort(s.loc[s.catalog == "FALSE POSITIVE", feature].dropna().values)
    return pl, fp


def nasa_url(kepoi: str) -> str:
    star, planet = kepoi[1:].split(".")
    return f"https://exoplanetarchive.ipac.caltech.edu/overview/KOI-{int(star)}.{planet}"


def spectral_class(teff) -> str:
    if pd.isna(teff):
        return "?"
    for limit, letter in [(3900, "M"), (5300, "K"), (6000, "G"), (7500, "F"),
                          (10000, "A")]:
        if teff < limit:
            return letter
    return "B"


try:
    BUNDLE, SCORES, AUDIT = load_artifacts()
except FileNotFoundError as e:
    st.error(f"Run the pipeline first (see README). Missing: {e.filename}")
    st.stop()

QHAT = BUNDLE["qhat"]

LITERATURE = {
    "K01450.01": ("⚖️ Verified catch", RED,
        "Catalog snapshot says CONFIRMED (Kepler-854 b). NASA <b>demoted it "
        "to false positive</b> after Niraula et al. 2022 revised its mass "
        "above 30 M_Jup. ExoJury flagged it at p = 0.00003 from this CSV alone."),
    "K01416.01": ("⚖️ Verified catch", RED,
        "Catalog snapshot says CONFIRMED (Kepler-840 b). Also <b>demoted by "
        "NASA</b> after the same 2022 mass revision. ExoJury: p = 0.0016."),
    "K07016.01": ("⚠️ Disputed in literature", YELLOW,
        "Kepler-452 b, 'Earth's cousin'. Its statistical validation was "
        "formally disputed (Mullally et al. 2018); with final DR25 data it "
        "no longer reaches 99% confidence. ExoJury: p = 0.0006."),
    "K03794.01": ("🤔 Honest miss", YELLOW,
        "Kepler-1520 b — a real but <i>disintegrating</i> planet. Its dusty, "
        "variable transits break the standard fit (fitted radius 23 R⊕), so "
        "the model scores it low. Physics weirder than the training set."),
    "K00701.03": ("🌍 Showpiece", BLUE,
        "Kepler-62 e — a confirmed super-Earth in the habitable zone, "
        "1.7 R⊕ at 270 K. ExoJury agrees with the catalog at >99.9%."),
}

# ------------------------------------------------------------------- hero
n_cand = int((SCORES.catalog == "CANDIDATE").sum())
st.iframe(ui.hero_html([
    ("9,564", "KOIs ON TRIAL"),
    ("98.2%", "HONEST ACCURACY"),
    ("95.6%", "CONFORMAL COVERAGE"),
    ("2", "NASA-VERIFIED CATCHES"),
    (f"{n_cand:,}", "CANDIDATES RANKED"),
]), height=312)

tab_trial, tab_frontier, tab_sky, tab_audit, tab_honesty, tab_how = st.tabs(
    ["⚖️ The Trial", "🚀 Frontier", "🌌 Sky Map", "🧾 The Audit",
     "📏 Honesty", "🧠 How it works"])

# ------------------------------------------------------------------ trial
with tab_trial:
    labels = SCORES.apply(
        lambda r: f"{r.kepoi_name} — {r.kepler_name}" if pd.notna(r.kepler_name)
        else f"{r.kepoi_name} ({r.catalog})", axis=1)
    default_idx = int(SCORES.index[SCORES.kepoi_name == "K00701.03"][0])

    sel = st.selectbox("Put a KOI on trial — search 9,564 objects",
                       SCORES.index.tolist(),
                       index=default_idx, format_func=lambda i: labels[i])
    row = SCORES.loc[sel]
    p = float(row.p_planet)
    color, icon, verdict_short = VERDICT_STYLE[row.verdict]
    p_label = ">99.9%" if p > 0.999 else ("<0.1%" if p < 0.001 else f"{p*100:.1f}%")
    agree = (
        "✓ agrees with catalog" if
        (row.verdict == row.catalog) or
        (verdict_short == "FALSE POSITIVE" and row.catalog == "FALSE POSITIVE")
        else ("• catalog undecided — this is a live prediction"
              if row.catalog == "CANDIDATE" else "⚡ disagrees with catalog")
    )

    left, right = st.columns([1.05, 1.6], gap="large")
    with left:
        st.markdown(f"""
        <div class="verdict-card" style="border-left: 5px solid {color};">
          <span class="chip" style="background:{rgba(color,.14)};color:{color};">{icon} VERDICT: {verdict_short}</span>
          <span class="chip" style="background:{rgba(CATALOG_COLOR[row.catalog],.14)};color:{CATALOG_COLOR[row.catalog]};">CATALOG: {row.catalog}</span>
          <div class="headline">p(planet) = {p_label}</div>
          <div class="sub">95% conformal prediction set · {agree}
          {"· <b>held-out — the model never trained on this object</b>" if row.unseen else ""}</div>
        </div>""", unsafe_allow_html=True)

        if row.kepoi_name in LITERATURE:
            tag, tcolor, note = LITERATURE[row.kepoi_name]
            st.markdown(f"""<div class="story" style="margin-bottom:12px;">
              <span class="tag" style="background:{rgba(tcolor,.14)};color:{tcolor};">{tag}</span>
              <p style="margin-top:8px;">{note}</p></div>""",
              unsafe_allow_html=True)

        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=p * 100,
            number=dict(suffix="%", valueformat=".1f",
                        font=dict(size=30, color=INK)),
            gauge=dict(
                axis=dict(range=[0, 100], showticklabels=False, ticks=""),
                bar=dict(color=INK, thickness=0.22),
                bgcolor=PANEL, borderwidth=0,
                steps=[
                    dict(range=[0, QHAT * 100], color=rgba(RED, 0.33)),
                    dict(range=[QHAT * 100, (1 - QHAT) * 100], color=rgba(YELLOW, 0.27)),
                    dict(range=[(1 - QHAT) * 100, 100], color=rgba(BLUE, 0.33)),
                ],
            )))
        fig.update_layout(**{**PLOTLY_LAYOUT, "height": 190,
                             "margin": dict(l=25, r=25, t=14, b=4)})
        st.plotly_chart(fig, config={"displayModeBar": False})
        st.caption("Gauge zones = conformal decision regions: red = false "
                   f"positive (≤{QHAT*100:.0f}%), amber = needs review, "
                   f"blue = planet (≥{(1-QHAT)*100:.0f}%).")

        st.link_button("🔗 NASA Exoplanet Archive record",
                       nasa_url(row.kepoi_name))

        if os.environ.get("FEATHERLESS_API_KEY"):
            cache_file = config.REPORTS_DIR / "dossiers" / f"{row.kepoi_name}.md"
            with st.expander("✍️ AI vetting dossier (Featherless · DeepSeek-V3)",
                             expanded=cache_file.exists()):
                if cache_file.exists():
                    st.markdown(cache_file.read_text())
                elif st.button("Write the dossier"):
                    from exojury.dossier import write_dossier
                    with st.spinner("The clerk is writing..."):
                        st.markdown(write_dossier(row.kepoi_name))
        else:
            st.info("Set FEATHERLESS_API_KEY to enable AI vetting dossiers.")

    with right:
        st.iframe(ui.system_viewer_html(
            row.koi_period, row.koi_prad, row.koi_srad, row.koi_steff,
            row.koi_teq, row.koi_depth, row.kepoi_name), height=402)

        def fmt(v, spec, dash="—"):
            return dash if pd.isna(v) else format(v, spec)
        chips = [
            f"🪐 radius <b>{fmt(row.koi_prad, '.2f')}× Earth</b>",
            f"📅 year = <b>{fmt(row.koi_period, '.2f')} days</b>",
            f"🌡️ T_eq <b>{fmt(row.koi_teq, '.0f')} K</b> (Earth ≈ 255 K)",
            f"☀️ insolation <b>{fmt(row.koi_insol, '.2f')}× Earth</b>",
            f"⭐ host: <b>{spectral_class(row.koi_steff)}-type</b>, "
            f"{fmt(row.koi_steff, '.0f')} K, {fmt(row.koi_srad, '.2f')} R☉",
            f"🔭 transit depth <b>{fmt(row.koi_depth, ',.0f')} ppm</b>",
            f"📡 SNR <b>{fmt(row.koi_model_snr, '.1f')}</b>",
            f"🛰️ signals on this star: <b>{fmt(row.koi_count, '.0f')}</b>",
        ]
        if pd.notna(row.koi_teq) and 180 <= row.koi_teq <= 310 and \
           pd.notna(row.koi_prad) and row.koi_prad <= 2:
            chips.append("🌍 <b>habitable-zone candidate</b> (T_eq 180–310 K, ≤2 R⊕)")
        st.markdown('<div class="info-chips">' + "".join(
            f'<span class="ichip">{c}</span>' for c in chips) + "</div>",
            unsafe_allow_html=True)

        st.markdown("**Evidence: this object's percentile inside each population**")
        EV_FEATS = [
            ("koi_prad", "Planet radius"),
            ("koi_depth", "Transit depth"),
            ("koi_model_snr", "Signal-to-noise"),
            ("duty_cycle", "Duty cycle"),
            ("dicco_offset_sig", "Centroid offset σ"),
            ("prad_over_srad", "Radius ratio"),
            ("koi_count", "Signals on star"),
        ]
        rows_pl, rows_fp, names = [], [], []
        for col, label in EV_FEATS:
            v = row[col]
            if pd.isna(v):
                continue
            pl, fp = class_percentiles(col)
            rows_pl.append(100 * np.searchsorted(pl, v) / max(len(pl), 1))
            rows_fp.append(100 * np.searchsorted(fp, v) / max(len(fp), 1))
            names.append(label)
        fig = go.Figure()
        fig.add_scatter(x=rows_pl, y=names, mode="markers", name="among planets",
                        marker=dict(color=BLUE, size=11))
        fig.add_scatter(x=rows_fp, y=names, mode="markers", name="among false positives",
                        marker=dict(color=RED, size=11, symbol="diamond"))
        for x0 in (5, 95):
            fig.add_vline(x=x0, line=dict(color=GRID, dash="dot", width=1))
        fig.update_layout(**PLOTLY_LAYOUT, height=280,
                          legend=dict(orientation="h", y=1.12, x=0))
        fig.update_xaxes(range=[-3, 103], title_text="percentile")
        st.plotly_chart(fig, config={"displayModeBar": False})

# --------------------------------------------------------------- frontier
with tab_frontier:
    cand = SCORES[SCORES.catalog == "CANDIDATE"].copy()
    f1, f2, f3 = st.columns([1.2, 1.4, 1])
    with f1:
        min_p = st.slider("Min calibrated p(planet)", 0.0, 1.0, 0.5, 0.01)
    with f2:
        verd = st.multiselect("Conformal verdict",
                              ["CONFIRMED", "NEEDS REVIEW (ambiguous)", "FALSE POSITIVE"],
                              default=["CONFIRMED", "NEEDS REVIEW (ambiguous)"])
    with f3:
        hz = st.toggle("🌍 Habitable-zone only")

    view = cand[(cand.p_planet >= min_p) & (cand.verdict.isin(verd))]
    if hz:
        view = view[(view.koi_teq.between(180, 310)) & (view.koi_prad <= 2.0)]
    st.markdown(f"**{len(view):,} candidates** match — sorted by calibrated "
                "probability. These are real, unresolved objects: nobody knows "
                "yet which are planets.")

    st.markdown("**The unresolved frontier — period vs radius**")
    fig = go.Figure()
    for verdict, vcolor in [("FALSE POSITIVE", RED),
                            ("NEEDS REVIEW (ambiguous)", YELLOW),
                            ("CONFIRMED", BLUE)]:
        sub = view[view.verdict == verdict]
        if len(sub) == 0:
            continue
        fig.add_scatter(
            x=sub.koi_period, y=sub.koi_prad, mode="markers",
            name=VERDICT_STYLE[verdict][2].title(),
            marker=dict(color=vcolor, size=6, opacity=0.75),
            customdata=np.stack([sub.kepoi_name, sub.p_planet,
                                 sub.koi_teq.fillna(-1)], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b><br>p(planet)=%{customdata[1]:.3f}"
                          "<br>period %{x:.2f} d · radius %{y:.2f} R⊕"
                          "<br>T_eq %{customdata[2]:.0f} K<extra></extra>")
    fig.update_layout(**PLOTLY_LAYOUT, height=380,
                      legend=dict(orientation="h", y=1.08, x=0))
    fig.update_xaxes(type="log", title_text="orbital period [days]",
                     tickvals=[0.5, 1, 3, 10, 30, 100, 300],
                     ticktext=["0.5", "1", "3", "10", "30", "100", "300"])
    fig.update_yaxes(type="log", title_text="planet radius [R⊕]",
                     tickvals=[0.5, 1, 2, 4, 8, 16, 32],
                     ticktext=["0.5", "1", "2", "4", "8", "16", "32"])
    st.plotly_chart(fig, config={"displayModeBar": False})

    table = view.sort_values("p_planet", ascending=False)[
        ["kepoi_name", "p_planet", "verdict", "koi_period", "koi_prad",
         "koi_teq", "koi_model_snr"]].copy()
    table["nasa"] = table["kepoi_name"].map(nasa_url)
    st.dataframe(
        table, width="stretch", height=380, hide_index=True,
        column_config={
            "kepoi_name": "KOI",
            "p_planet": st.column_config.ProgressColumn(
                "p(planet)", format="%.3f", min_value=0, max_value=1),
            "verdict": "conformal verdict",
            "koi_period": st.column_config.NumberColumn("period [d]", format="%.2f"),
            "koi_prad": st.column_config.NumberColumn("radius [R⊕]", format="%.2f"),
            "koi_teq": st.column_config.NumberColumn("T_eq [K]", format="%d"),
            "koi_model_snr": st.column_config.NumberColumn("SNR", format="%.1f"),
            "nasa": st.column_config.LinkColumn("archive", display_text="NASA ↗"),
        })
    st.download_button("⬇ Download this list (CSV)", table.to_csv(index=False),
                       "exojury_frontier.csv")

# ---------------------------------------------------------------- sky map
with tab_sky:
    mode = st.radio("View", ["2D field · verdict", "2D field · probability",
                             "3D · brightness depth"],
                    horizontal=True, label_visibility="collapsed")
    fig = go.Figure()
    if mode == "2D field · verdict":
        for verdict, vcolor in [("FALSE POSITIVE", RED),
                                ("NEEDS REVIEW (ambiguous)", YELLOW),
                                ("NEEDS REVIEW (both plausible)", YELLOW),
                                ("CONFIRMED", BLUE)]:
            sub = SCORES[SCORES.verdict == verdict]
            if len(sub) == 0:
                continue
            fig.add_scattergl(
                x=sub.ra, y=sub.dec, mode="markers",
                name=VERDICT_STYLE[verdict][2].title(),
                marker=dict(color=vcolor, size=4, opacity=0.55),
                customdata=np.stack([sub.kepoi_name, sub.p_planet], axis=-1),
                hovertemplate="<b>%{customdata[0]}</b> · p=%{customdata[1]:.3f}"
                              "<br>RA %{x:.3f}° · Dec %{y:.3f}°<extra></extra>")
        height = 560
    elif mode == "2D field · probability":
        fig.add_scattergl(
            x=SCORES.ra, y=SCORES.dec, mode="markers",
            marker=dict(color=SCORES.p_planet, colorscale=[
                [0, "#cde2fb"], [0.5, "#3987e5"], [1, "#0d366b"]],
                size=4, opacity=0.7,
                colorbar=dict(title="p(planet)", tickcolor=MUTED)),
            customdata=np.stack([SCORES.kepoi_name, SCORES.p_planet], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b> · p=%{customdata[1]:.3f}<extra></extra>")
        height = 560
    else:
        groups = [
            ("FALSE POSITIVE", SCORES[SCORES.verdict == "FALSE POSITIVE"], RED),
            ("NEEDS REVIEW", SCORES[SCORES.verdict.str.startswith("NEEDS")], YELLOW),
            ("PLANET", SCORES[SCORES.verdict == "CONFIRMED"], BLUE),
        ]
        for gname, sub, vcolor in groups:
            if len(sub) == 0:
                continue
            fig.add_scatter3d(
                x=sub.ra, y=sub.dec, z=sub.koi_kepmag, mode="markers",
                name=gname.title(),
                marker=dict(color=vcolor, size=1.6, opacity=0.6),
                customdata=np.stack([sub.kepoi_name, sub.p_planet], axis=-1),
                hovertemplate="<b>%{customdata[0]}</b> · p=%{customdata[1]:.3f}"
                              "<br>Kp %{z:.1f}<extra></extra>")
        fig.update_layout(scene=dict(
            xaxis=dict(title="RA [°]", backgroundcolor=PANEL, gridcolor=GRID,
                       autorange="reversed"),
            yaxis=dict(title="Dec [°]", backgroundcolor=PANEL, gridcolor=GRID),
            zaxis=dict(title="brightness [Kp mag]", backgroundcolor=PANEL,
                       gridcolor=GRID, autorange="reversed"),
            bgcolor=PANEL,
        ))
        height = 640
    fig.update_layout(**{**PLOTLY_LAYOUT,
                         "margin": dict(l=10, r=10, t=76, b=10)},
                      height=height,
                      title=dict(text="Kepler's field of view — 9,564 objects of interest "
                                      "(Cygnus–Lyra, ~10°×10°)",
                                 font=dict(size=13, color=INK), y=0.97),
                      legend=dict(orientation="h", y=1.045, x=0))
    if mode.startswith("2D"):
        fig.update_xaxes(title_text="right ascension [°]", autorange="reversed")
        fig.update_yaxes(title_text="declination [°]", scaleanchor="x")
    st.plotly_chart(fig, config={"displayModeBar": mode.startswith("3D")})
    st.caption("Every dot is a transit-like signal Kepler flagged between "
               "2009–2018. In 2D, zoom in — the 21 CCD module gaps are visible "
               "as empty stripes. In 3D, drag to rotate: depth = apparent "
               "brightness (brightest stars on top).")

# -------------------------------------------------------------- the audit
with tab_audit:
    st.markdown("### The model auditing its own teachers")
    st.markdown(
        "Confident learning asks: *which catalog labels does an out-of-fold "
        "model most confidently disagree with?* We checked the top flags "
        "against the literature **after** the model produced them.")
    c1, c2, c3 = st.columns(3, gap="medium")
    for col, koi in [(c1, "K01450.01"), (c2, "K01416.01"), (c3, "K07016.01")]:
        tag, tcolor, note = LITERATURE[koi]
        r = SCORES[SCORES.kepoi_name == koi].iloc[0]
        name = r.kepler_name if pd.notna(r.kepler_name) else koi
        with col:
            st.markdown(f"""<div class="story">
              <span class="tag" style="background:{rgba(tcolor,.14)};color:{tcolor};">{tag}</span>
              <h4 style="margin-top:8px;">{name} <span style="color:{MUTED};font-weight:400;">({koi})</span></h4>
              <p>{note}</p></div>""", unsafe_allow_html=True)
    st.markdown("")
    st.markdown("**All 46 flags** (0.6% of labeled rows), ranked by model confidence:")
    st.dataframe(
        AUDIT, width="stretch", height=420, hide_index=True,
        column_config={
            "p_planet_oof": st.column_config.ProgressColumn(
                "p(planet), out-of-fold", format="%.4f", min_value=0, max_value=1),
        })

# ---------------------------------------------------------------- honesty
with tab_honesty:
    st.markdown("### Why our accuracy is lower than theirs — on purpose")
    st.markdown(
        "The KOI table contains NASA's own vetting outputs. `kepler_name` + "
        "`koi_pdisposition` reconstruct the answer with **99.96% accuracy and "
        "zero ML**; the Robovetter `fpflag` columns alone give 98.5%. ExoJury "
        "excludes every such column under a documented per-column policy "
        "(`src/exojury/config.py`) — and *measures* the inflation instead of "
        "shipping it: **+1.3 accuracy points**.")
    a, b = st.columns(2, gap="large")
    with a:
        st.image("reports/figures/dark/04_leakage_answer_key.png",
                 caption="The answer key hiding in the dataset")
        st.image("reports/figures/dark/06_reliability.png",
                 caption="Calibration: when ExoJury says 90%, it happens ~90% of the time (ECE 0.009)")
    with b:
        st.image("reports/figures/dark/07_conformal_verdicts.png",
                 caption="Conformal verdicts: 95.6% empirical coverage vs 95% target. "
                         "On the truly-unresolved frontier the model abstains 3× more often — "
                         "it knows those are harder.")
        st.image("reports/figures/dark/05_confusion_3class.png",
                 caption="Challenge-required 3-class model (86.1% acc). CANDIDATE is the "
                         "weak class because it's a state of knowledge, not a kind of object.")

# ----------------------------------------------------------- how it works
with tab_how:
    st.markdown("### The pipeline, start to finish")
    steps = [
        ("1 · Leakage audit", "All 140 columns assigned to documented tiers; "
         "everything NASA's vetting wrote (names, dispositions, comments, "
         "Robovetter flags) is excluded. The 'answer key' alone scores 99.96% "
         "with zero ML — that's what we refuse to copy."),
        ("2 · Honest model", "Gradient boosting (scikit-learn "
         "HistGradientBoosting) on 105 physics features — transit shape, "
         "centroid offsets, stellar properties — plus engineered features "
         "like duty cycle and depth-vs-radius-ratio consistency. 98.2% "
         "held-out accuracy, ROC-AUC 0.997."),
        ("3 · Calibration", "Isotonic regression on cross-validated "
         "predictions makes probabilities mean what they say "
         "(expected calibration error 0.009)."),
        ("4 · Conformal guarantee", "Split conformal prediction on a "
         "held-aside slice: every object gets a prediction set that contains "
         "the truth ≥95% of the time (empirically 95.6%). Empty set ⇒ "
         "NEEDS REVIEW — the model abstains instead of guessing."),
        ("5 · Label audit", "cleanlab confident learning flags catalog "
         "labels the out-of-fold model disagrees with — it found two planets "
         "NASA later demoted, from this CSV alone."),
        ("6 · The frontier", "The 1,978 unresolved CANDIDATEs scored and "
         "ranked: 335 planet-like (95% guarantee), 1,125 false-positive-like, "
         "518 for human review — a telescope-time priority list."),
        ("7 · AI dossiers", "DeepSeek-V3 via Featherless.ai narrates each "
         "verdict as a SIGNAL / ASSESSMENT / FOLLOW-UP report, grounded "
         "strictly in the pipeline's numbers. The model decides; the LLM writes."),
    ]
    cols = st.columns(2, gap="medium")
    for i, (title, body) in enumerate(steps):
        with cols[i % 2]:
            st.markdown(f"""<div class="story" style="margin-bottom:12px;">
              <h4>{title}</h4><p>{body}</p></div>""", unsafe_allow_html=True)

    st.markdown("### Glossary — the words on this dashboard")
    GLOSSARY = {
        "KOI": "Kepler Object of Interest — a periodic dimming signal that "
               "might be a planet crossing its star.",
        "Transit depth (ppm)": "How much starlight the object blocks, in "
               "parts per million. Earth crossing the Sun: ~84 ppm.",
        "Impact parameter": "How centrally the object crosses the star; "
               ">1 means it barely grazes — a binary-star signature.",
        "Centroid offset σ": "How far the light's centre shifts during "
               "transit. Big shifts mean the dimming comes from a background "
               "star, not the target.",
        "Odd–even test": "Eclipsing binaries show alternating deep/shallow "
               "events; planets don't.",
        "Duty cycle": "Fraction of the orbit spent in transit — physically "
               "constrained for true planets.",
        "Calibrated probability": "A probability that means what it says: "
               "of all objects given 90%, ~90% are planets.",
        "Conformal prediction": "A distribution-free wrapper that turns "
               "scores into prediction sets with a finite-sample coverage "
               "guarantee — our 95% is math, not vibes.",
        "Abstention / NEEDS REVIEW": "When neither label fits at 95% "
               "confidence, the pipeline hands the object to a human "
               "instead of guessing.",
        "Confident learning": "Using out-of-fold predictions to find "
               "training labels that are probably wrong (cleanlab).",
        "Leakage": "Any feature computed from the answer. The KOI table "
               "is full of it; most models trained on it are partly "
               "grading themselves with the answer key.",
    }
    g1, g2 = st.columns(2, gap="medium")
    items = list(GLOSSARY.items())
    for i, (term, defn) in enumerate(items):
        with (g1 if i < (len(items) + 1) // 2 else g2):
            st.markdown(f"**{term}** — {defn}")

    st.markdown("### Data & reproducibility")
    st.markdown(
        "- **Data**: NASA Exoplanet Archive, KOI cumulative table "
        "(DOI 10.26133/NEA4) — 9,564 rows × 140 columns, provided by the "
        "Celesta challenge. Data by the NASA Exoplanet Science Institute at "
        "IPAC/Caltech.\n"
        "- **Reproduce**: every figure and number regenerates from the "
        "commands in `README.md`; all random seeds fixed.\n"
        "- **Honest limitations**: the model sees fitted parameters, not raw "
        "light curves; the catalog snapshot predates post-2018 revisions "
        "(which is exactly how the audit could be verified); the "
        "habitable-zone tag is a coarse T_eq heuristic; and a few features "
        "(e.g. stellar-parameter uncertainties) may partly encode observation "
        "effort rather than physics.")
