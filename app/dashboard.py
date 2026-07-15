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

st.set_page_config(page_title="ExoJury", page_icon="🪐", layout="wide",
                   initial_sidebar_state="collapsed")

# ---------------------------------------------------------------- palette
# dataviz reference palette, dark mode
SURFACE = "#1a1a19"
PAGE = "#0d0d0d"
INK = "#ffffff"
INK2 = "#c3c2b7"
MUTED = "#898781"
GRID = "#2c2c2a"
BLUE = "#3987e5"    # planet / confirmed
YELLOW = "#c98500"  # needs review / candidate
RED = "#e66767"     # false positive

VERDICT_STYLE = {
    "CONFIRMED": (BLUE, "🪐", "PLANET"),
    "FALSE POSITIVE": (RED, "✖", "FALSE POSITIVE"),
    "NEEDS REVIEW (ambiguous)": (YELLOW, "🔍", "NEEDS REVIEW"),
    "NEEDS REVIEW (both plausible)": (YELLOW, "🔍", "NEEDS REVIEW"),
}
CATALOG_COLOR = {"CONFIRMED": BLUE, "CANDIDATE": YELLOW, "FALSE POSITIVE": RED}


def rgba(hex_color: str, a: float) -> str:
    """Plotly-safe translucent color (plotly rejects 8-digit hex)."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{a})"

st.markdown(f"""<style>
.block-container {{ padding-top: 1.6rem; max-width: 1250px; }}
.hero-title {{ font-size: 2.3rem; font-weight: 800; letter-spacing: -.02em;
  margin-bottom: .1rem; }}
.hero-sub {{ color: {INK2}; font-size: 1.02rem; margin-bottom: 1.1rem; }}
.kpi-row {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: .4rem; }}
.kpi {{ flex: 1 1 200px; background: {SURFACE}; border: 1px solid rgba(255,255,255,.10);
  border-radius: 12px; padding: 14px 18px; }}
.kpi .v {{ font-size: 1.65rem; font-weight: 700; }}
.kpi .l {{ color: {MUTED}; font-size: .82rem; margin-top: 2px; }}
.verdict-card {{ border-radius: 14px; padding: 18px 22px; margin: 6px 0 14px 0;
  border: 1px solid rgba(255,255,255,.12); background: {SURFACE}; }}
.verdict-card .headline {{ font-size: 1.5rem; font-weight: 800; }}
.verdict-card .sub {{ color: {INK2}; font-size: .95rem; margin-top: 4px; }}
.chip {{ display: inline-block; padding: 3px 12px; border-radius: 999px;
  font-size: .8rem; font-weight: 700; margin-right: 8px; }}
.story {{ background: {SURFACE}; border: 1px solid rgba(255,255,255,.10);
  border-radius: 12px; padding: 16px 18px; height: 100%; }}
.story h4 {{ margin: 0 0 6px 0; font-size: 1.02rem; }}
.story p {{ color: {INK2}; font-size: .88rem; margin: 4px 0; }}
.story .tag {{ font-size: .75rem; font-weight: 700; padding: 2px 10px;
  border-radius: 999px; }}
</style>""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(color=INK2, family="system-ui, -apple-system, sans-serif", size=12),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#383835"),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#383835"),
    margin=dict(l=10, r=10, t=42, b=10),
)

# ---------------------------------------------------------------- artifacts

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


try:
    BUNDLE, SCORES, AUDIT = load_artifacts()
except FileNotFoundError as e:
    st.error(f"Run the pipeline first (see README). Missing: {e.filename}")
    st.stop()

QHAT = BUNDLE["qhat"]

# Literature notes for showcase objects (verified via NASA archive / ADS)
LITERATURE = {
    "K01450.01": ("⚖️ Verified catch", RED,
        "Catalog snapshot says CONFIRMED (Kepler-854 b). NASA **demoted it to "
        "false positive** after Niraula et al. 2022 revised its mass above "
        "30 M_Jup. ExoJury flagged it at p = 0.00003 from this CSV alone."),
    "K01416.01": ("⚖️ Verified catch", RED,
        "Catalog snapshot says CONFIRMED (Kepler-840 b). Also **demoted by "
        "NASA** after the same 2022 mass revision. ExoJury: p = 0.0016."),
    "K07016.01": ("⚠️ Disputed in literature", YELLOW,
        "Kepler-452 b, 'Earth's cousin'. Its statistical validation was "
        "formally disputed (Mullally et al. 2018); with final DR25 data it "
        "no longer reaches 99% confidence. ExoJury: p = 0.0006."),
    "K03794.01": ("🤔 Honest miss", YELLOW,
        "Kepler-1520 b — a real but *disintegrating* planet. Its dusty, "
        "variable transits break the standard fit (fitted radius 23 R⊕), so "
        "the model scores it low. Physics weirder than the training set."),
    "K00701.03": ("🌍 Showpiece", BLUE,
        "Kepler-62 e — a confirmed super-Earth in the habitable zone, "
        "1.7 R⊕ at 270 K. ExoJury agrees with the catalog at >99.9%."),
}

# ---------------------------------------------------------------- hero

st.markdown('<div class="hero-title">🪐⚖️ ExoJury</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Every Kepler candidate gets a fair trial — '
            'a calibrated verdict, a 95% statistical guarantee, and a written '
            'opinion. Leakage-audited, physics only.</div>', unsafe_allow_html=True)

n_review = int((SCORES.catalog == "CANDIDATE").sum())
kpis = [
    ("9,564", "KOIs on trial"),
    ("98.2%", "honest test accuracy (leakage-free)"),
    ("95.6%", "conformal coverage (target 95%)"),
    ("2", "NASA-verified catalog errors found"),
    (f"{n_review:,}", "unresolved candidates ranked"),
]
st.markdown('<div class="kpi-row">' + "".join(
    f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div></div>'
    for v, l in kpis) + "</div>", unsafe_allow_html=True)

tab_trial, tab_frontier, tab_sky, tab_audit, tab_honesty = st.tabs(
    ["⚖️ The Trial", "🚀 Frontier", "🌌 Sky Map", "🧾 The Audit", "📏 Honesty"])

# ---------------------------------------------------------------- the trial

with tab_trial:
    left, right = st.columns([1.05, 1.6], gap="large")

    labels = SCORES.apply(
        lambda r: f"{r.kepoi_name} — {r.kepler_name}" if pd.notna(r.kepler_name)
        else f"{r.kepoi_name} ({r.catalog})", axis=1)
    default_idx = int(SCORES.index[SCORES.kepoi_name == "K00701.03"][0])

    with left:
        sel = st.selectbox("Put a KOI on trial", SCORES.index.tolist(),
                           index=default_idx, format_func=lambda i: labels[i])
        row = SCORES.loc[sel]
        p = float(row.p_planet)
        color, icon, verdict_short = VERDICT_STYLE[row.verdict]
        p_label = ">99.9%" if p > 0.999 else ("<0.1%" if p < 0.001 else f"{p*100:.1f}%")
        agree = (
            "✓ agrees with catalog" if
            (row.verdict == row.catalog) or
            (verdict_short == "FALSE POSITIVE" and row.catalog == "FALSE POSITIVE")
            else ("• catalog undecided" if row.catalog == "CANDIDATE"
                  else "⚡ disagrees with catalog")
        )
        st.markdown(f"""
        <div class="verdict-card" style="border-left: 6px solid {color};">
          <span class="chip" style="background:{color}22;color:{color};">{icon} VERDICT: {verdict_short}</span>
          <span class="chip" style="background:{CATALOG_COLOR[row.catalog]}22;color:{CATALOG_COLOR[row.catalog]};">CATALOG: {row.catalog}</span>
          <div class="headline">p(planet) = {p_label}</div>
          <div class="sub">95% conformal prediction set · {agree}
          {"· <b>held-out object — the model never trained on it</b>" if row.unseen else ""}</div>
        </div>""", unsafe_allow_html=True)

        if row.kepoi_name in LITERATURE:
            tag, tcolor, note = LITERATURE[row.kepoi_name]
            st.markdown(f"""<div class="story" style="margin-bottom:12px;">
              <span class="tag" style="background:{tcolor}22;color:{tcolor};">{tag}</span>
              <p style="margin-top:8px;">{note}</p></div>""",
              unsafe_allow_html=True)

        # conformal gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=p * 100,
            number=dict(suffix="%", valueformat=".1f",
                        font=dict(size=30, color=INK)),
            gauge=dict(
                axis=dict(range=[0, 100], showticklabels=False, ticks=""),
                bar=dict(color=INK, thickness=0.22),
                bgcolor=SURFACE, borderwidth=0,
                steps=[
                    dict(range=[0, QHAT * 100], color=rgba(RED, 0.33)),
                    dict(range=[QHAT * 100, (1 - QHAT) * 100], color=rgba(YELLOW, 0.27)),
                    dict(range=[(1 - QHAT) * 100, 100], color=rgba(BLUE, 0.33)),
                ],
            )))
        fig.update_layout(**{**PLOTLY_LAYOUT, "height": 200,
                             "margin": dict(l=25, r=25, t=14, b=6)})
        st.plotly_chart(fig, config={"displayModeBar": False})
        st.caption("Gauge zones are the conformal decision regions: "
                   f"red = false positive (≤{QHAT*100:.0f}%), amber = needs "
                   f"review, blue = planet (≥{(1-QHAT)*100:.0f}%).")

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
        # schematic transit from fitted parameters
        depth = row.koi_depth if pd.notna(row.koi_depth) else 0.0
        dur = row.koi_duration if pd.notna(row.koi_duration) else 3.0
        b = min(float(row.koi_impact), 1.2) if pd.notna(row.koi_impact) else 0.3
        flat_frac = float(np.clip(1.0 - b, 0.03, 0.9))
        d_rel = depth / 1e6
        t = np.array([-1.6 * dur, -dur / 2, -dur / 2 * flat_frac,
                      dur / 2 * flat_frac, dur / 2, 1.6 * dur])
        f = np.array([0, 0, -d_rel, -d_rel, 0, 0]) * 100
        fig = go.Figure()
        fig.add_scatter(x=t, y=f, mode="lines", line=dict(color=BLUE, width=2.5),
                        fill="tozeroy", fillcolor=rgba(BLUE, 0.15),
                        hovertemplate="t = %{x:.1f} h<br>Δflux = %{y:.4f}%<extra></extra>")
        fig.update_layout(**PLOTLY_LAYOUT, height=240,
                          title=dict(text="Schematic transit (from fitted parameters)",
                                     font=dict(size=13, color=INK)))
        fig.update_xaxes(title_text="hours from mid-transit")
        fig.update_yaxes(title_text="flux change [%]")
        st.plotly_chart(fig, config={"displayModeBar": False})
        st.caption(f"Depth {depth:,.0f} ppm · duration {dur:.2f} h · "
                   f"impact parameter {row.koi_impact if pd.notna(row.koi_impact) else '—'} · "
                   f"period {row.koi_period:.4g} d — drawn from the table's fit, "
                   "not real flux data.")

        # evidence: where does this object sit in each population?
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
        st.markdown("**Evidence: this object's percentile inside each population**")
        fig = go.Figure()
        fig.add_scatter(x=rows_pl, y=names, mode="markers", name="among planets",
                        marker=dict(color=BLUE, size=11))
        fig.add_scatter(x=rows_fp, y=names, mode="markers", name="among false positives",
                        marker=dict(color=RED, size=11, symbol="diamond"))
        for x0 in (5, 95):
            fig.add_vline(x=x0, line=dict(color=GRID, dash="dot", width=1))
        fig.update_layout(**{**PLOTLY_LAYOUT,
                             "margin": dict(l=10, r=10, t=34, b=10)},
                          height=300,
                          legend=dict(orientation="h", y=1.12, x=0))
        fig.update_xaxes(range=[-3, 103], title_text="percentile")
        st.plotly_chart(fig, config={"displayModeBar": False})
        st.caption("A value near 0 or 100 for a population means "
                   "\"extreme / atypical\" of that population. Typical-of-planets "
                   "and extreme-for-false-positives ⇒ evidence for a planet.")

# ---------------------------------------------------------------- frontier

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
    for verdict, color in [("FALSE POSITIVE", RED),
                           ("NEEDS REVIEW (ambiguous)", YELLOW),
                           ("CONFIRMED", BLUE)]:
        sub = view[view.verdict == verdict]
        if len(sub) == 0:
            continue
        fig.add_scatter(
            x=sub.koi_period, y=sub.koi_prad, mode="markers",
            name=VERDICT_STYLE[verdict][2].title(),
            marker=dict(color=color, size=6, opacity=0.75),
            customdata=np.stack([sub.kepoi_name, sub.p_planet,
                                 sub.koi_teq.fillna(-1)], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b><br>p(planet)=%{customdata[1]:.3f}"
                          "<br>period %{x:.2f} d · radius %{y:.2f} R⊕"
                          "<br>T_eq %{customdata[2]:.0f} K<extra></extra>")
    fig.update_layout(**{**PLOTLY_LAYOUT,
                         "margin": dict(l=10, r=10, t=34, b=10)},
                      height=380,
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
         "koi_teq", "koi_model_snr"]]
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
        })
    st.download_button("⬇ Download this list (CSV)", table.to_csv(index=False),
                       "exojury_frontier.csv")

# ---------------------------------------------------------------- sky map

with tab_sky:
    color_by = st.radio("Colour by", ["Conformal verdict", "Calibrated probability"],
                        horizontal=True, label_visibility="collapsed")
    fig = go.Figure()
    if color_by == "Conformal verdict":
        for verdict, color in [("FALSE POSITIVE", RED),
                               ("NEEDS REVIEW (ambiguous)", YELLOW),
                               ("NEEDS REVIEW (both plausible)", YELLOW),
                               ("CONFIRMED", BLUE)]:
            sub = SCORES[SCORES.verdict == verdict]
            if len(sub) == 0:
                continue
            fig.add_scattergl(
                x=sub.ra, y=sub.dec, mode="markers",
                name=VERDICT_STYLE[verdict][2].title(),
                marker=dict(color=color, size=4, opacity=0.55),
                customdata=np.stack([sub.kepoi_name, sub.p_planet], axis=-1),
                hovertemplate="<b>%{customdata[0]}</b> · p=%{customdata[1]:.3f}"
                              "<br>RA %{x:.3f}° · Dec %{y:.3f}°<extra></extra>")
    else:
        fig.add_scattergl(
            x=SCORES.ra, y=SCORES.dec, mode="markers",
            marker=dict(color=SCORES.p_planet, colorscale=[
                [0, "#cde2fb"], [0.5, "#3987e5"], [1, "#0d366b"]],
                size=4, opacity=0.7,
                colorbar=dict(title="p(planet)", tickcolor=MUTED)),
            customdata=np.stack([SCORES.kepoi_name, SCORES.p_planet], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b> · p=%{customdata[1]:.3f}<extra></extra>")
    fig.update_layout(**{**PLOTLY_LAYOUT,
                         "margin": dict(l=10, r=10, t=76, b=10)},
                      height=560,
                      title=dict(text="Kepler's field of view — 9,564 objects of interest "
                                      "(Cygnus–Lyra, ~10°×10°)",
                                 font=dict(size=13, color=INK), y=0.97),
                      legend=dict(orientation="h", y=1.045, x=0))
    fig.update_xaxes(title_text="right ascension [°]", autorange="reversed")
    fig.update_yaxes(title_text="declination [°]", scaleanchor="x")
    st.plotly_chart(fig, config={"displayModeBar": False})
    st.caption("Every dot is a transit-like signal Kepler flagged between "
               "2009–2018. Zoom in — the 21 CCD module gaps are visible as "
               "empty stripes.")

# ---------------------------------------------------------------- the audit

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
              <span class="tag" style="background:{tcolor}22;color:{tcolor};">{tag}</span>
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
    st.markdown(
        "**Method in one line:** gradient boosting on 105 physics features → "
        "isotonic calibration → split conformal prediction (95% guarantee, "
        "abstains when ambiguous) → cleanlab audit of the labels themselves → "
        "LLM narration via Featherless. Every seed fixed; every claim "
        "reproducible from `README.md`.")
