"""The Trial: one object, full verdict."""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ui
from common import (BLUE, CATALOG_COLOR, INK, LITERATURE, MUTED, PANEL,
                    PLOTLY_LAYOUT, RED, VERDICT_STYLE, YELLOW,
                    class_percentiles, config, load_artifacts, nasa_url,
                    rgba, section, spectral_class)

GRID = "#23262d"


def page():
    bundle, scores, _ = load_artifacts()
    qhat = bundle["qhat"]

    section("The Trial", "Put a world on trial",
            "Pick any of the 9,564 Kepler Objects of Interest. The verdict, "
            "the guarantee and the evidence update live.")

    labels = scores.apply(
        lambda r: f"{r.kepoi_name} — {r.kepler_name}" if pd.notna(r.kepler_name)
        else f"{r.kepoi_name} ({r.catalog})", axis=1)
    default_idx = int(scores.index[scores.kepoi_name == "K00701.03"][0])
    sel = st.selectbox("Search objects", scores.index.tolist(),
                       index=default_idx, format_func=lambda i: labels[i],
                       label_visibility="collapsed")
    row = scores.loc[sel]
    p = float(row.p_planet)
    color, verdict_short = VERDICT_STYLE[row.verdict]
    p_label = ">99.9%" if p > 0.999 else ("<0.1%" if p < 0.001 else f"{p*100:.1f}%")
    agree = (
        "✓ agrees with catalog" if
        (row.verdict == row.catalog) or
        (verdict_short == "FALSE POSITIVE" and row.catalog == "FALSE POSITIVE")
        else ("catalog undecided — this is a live prediction"
              if row.catalog == "CANDIDATE" else "⚡ disagrees with catalog")
    )

    left, right = st.columns([1, 1.55], gap="large")

    with left:
        st.markdown(f"""
        <div class="verdict-card" style="border-left: 4px solid {color};">
          <span class="chip" style="background:{rgba(color,.13)};color:{color};">VERDICT: {verdict_short}</span>
          <span class="chip" style="background:{rgba(CATALOG_COLOR[row.catalog],.13)};color:{CATALOG_COLOR[row.catalog]};">CATALOG: {row.catalog}</span>
          <div class="headline">p(planet) = {p_label}</div>
          <div class="sub">95% conformal prediction set · {agree}
          {"· <b>held-out object</b>" if row.unseen else ""}</div>
        </div>""", unsafe_allow_html=True)

        if row.kepoi_name in LITERATURE:
            tag, tcolor, note = LITERATURE[row.kepoi_name]
            st.markdown(f"""<div class="card" style="margin-bottom:12px;">
              <span class="tag" style="background:{rgba(tcolor,.13)};color:{tcolor};">{tag}</span>
              <p style="margin-top:8px;">{note}</p></div>""",
              unsafe_allow_html=True)

        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=p * 100,
            number=dict(suffix="%", valueformat=".1f",
                        font=dict(size=28, color=INK)),
            gauge=dict(
                axis=dict(range=[0, 100], showticklabels=False, ticks=""),
                bar=dict(color=INK, thickness=0.22),
                bgcolor=PANEL, borderwidth=0,
                steps=[
                    dict(range=[0, qhat * 100], color=rgba(RED, 0.30)),
                    dict(range=[qhat * 100, (1 - qhat) * 100], color=rgba(YELLOW, 0.24)),
                    dict(range=[(1 - qhat) * 100, 100], color=rgba(BLUE, 0.30)),
                ],
            )))
        fig.update_layout(**{**PLOTLY_LAYOUT, "height": 180,
                             "margin": dict(l=25, r=25, t=12, b=4)})
        st.plotly_chart(fig, config={"displayModeBar": False})
        st.caption(f"Gauge zones = conformal decision regions: "
                   f"≤{qhat*100:.0f}% false positive · middle needs review · "
                   f"≥{(1-qhat)*100:.0f}% planet.")
        st.link_button("NASA Exoplanet Archive record ↗", nasa_url(row.kepoi_name))

    with right:
        st.iframe(ui.system_viewer_html(
            row.koi_period, row.koi_prad, row.koi_srad, row.koi_steff,
            row.koi_teq, row.koi_depth), height=390)

    # -------- facts grid (full width, no chip soup, never overlaps)
    def fmt(v, spec):
        return "—" if pd.isna(v) else format(v, spec)
    facts = [
        ("Radius", f"{fmt(row.koi_prad, '.2f')}× Earth"),
        ("Year length", f"{fmt(row.koi_period, '.2f')} days"),
        ("Equilibrium temp", f"{fmt(row.koi_teq, '.0f')} K · Earth ≈ 255 K"),
        ("Insolation", f"{fmt(row.koi_insol, '.2f')}× Earth"),
        ("Host star", f"{spectral_class(row.koi_steff)}-type · "
                      f"{fmt(row.koi_steff, '.0f')} K · {fmt(row.koi_srad, '.2f')} R☉"),
        ("Transit depth", f"{fmt(row.koi_depth, ',.0f')} ppm"),
        ("Signal-to-noise", fmt(row.koi_model_snr, ".1f")),
        ("Signals on this star", fmt(row.koi_count, ".0f")),
    ]
    if pd.notna(row.koi_teq) and 180 <= row.koi_teq <= 310 and \
       pd.notna(row.koi_prad) and row.koi_prad <= 2:
        facts.append(("Habitable zone", "✓ candidate (T_eq 180–310 K, ≤2 R⊕)"))
    st.markdown('<div class="kv">' + "".join(
        f'<div><div class="k">{k}</div><div class="val">{v}</div></div>'
        for k, v in facts) + "</div>", unsafe_allow_html=True)

    ev_col, ai_col = st.columns([1.5, 1], gap="large")
    with ev_col:
        st.markdown("**Evidence — percentile inside each population**")
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
                        marker=dict(color=BLUE, size=10))
        fig.add_scatter(x=rows_fp, y=names, mode="markers",
                        name="among false positives",
                        marker=dict(color=RED, size=10, symbol="diamond"))
        for x0 in (5, 95):
            fig.add_vline(x=x0, line=dict(color=GRID, dash="dot", width=1))
        fig.update_layout(**{**PLOTLY_LAYOUT,
                             "margin": dict(l=10, r=10, t=44, b=10)},
                          height=290,
                          legend=dict(orientation="h", y=1.16, x=0))
        fig.update_xaxes(range=[-3, 103], title_text="percentile")
        st.plotly_chart(fig, config={"displayModeBar": False})
        st.caption("Near 0 or 100 = atypical of that population. "
                   "Typical-of-planets + extreme-for-false-positives ⇒ "
                   "evidence for a planet.")

    with ai_col:
        st.markdown("**AI vetting dossier** · Featherless / DeepSeek-V3")
        if os.environ.get("FEATHERLESS_API_KEY"):
            cache_file = config.REPORTS_DIR / "dossiers" / f"{row.kepoi_name}.md"
            if cache_file.exists():
                st.markdown(cache_file.read_text())
            elif st.button("Write the dossier"):
                from exojury.dossier import write_dossier
                try:
                    with st.spinner("The clerk is writing..."):
                        st.markdown(write_dossier(row.kepoi_name))
                except Exception as e:
                    if "401" in str(e) or "Authentication" in type(e).__name__:
                        st.error("Featherless rejected the API key. Check the "
                                 "FEATHERLESS_API_KEY secret (Manage app → "
                                 "Settings → Secrets) — it must be the exact "
                                 "key from featherless.ai → API Keys.")
                    else:
                        st.error(f"Dossier generation failed: "
                                 f"{type(e).__name__}. The model may be cold — "
                                 "try again in a few seconds.")
            else:
                st.caption("No cached dossier for this object — click to "
                           "generate one live.")
        else:
            st.info("Set FEATHERLESS_API_KEY to enable AI vetting dossiers.")
