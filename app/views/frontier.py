"""Frontier: the 1,978 unresolved candidates, ranked."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from common import (BLUE, PLOTLY_LAYOUT, RED, VERDICT_STYLE, YELLOW,
                    load_artifacts, nasa_url, section)


def page():
    _, scores, _ = load_artifacts()
    cand = scores[scores.catalog == "CANDIDATE"].copy()

    section("Frontier", "1,978 worlds nobody has resolved",
            "NASA's catalog still lists these as CANDIDATE. ExoJury scores "
            "every one — a ready-made telescope-time priority list.")

    f1, f2, f3 = st.columns([1.2, 1.6, 1], gap="medium")
    with f1:
        min_p = st.slider("Min calibrated p(planet)", 0.0, 1.0, 0.5, 0.01)
    with f2:
        verd = st.multiselect("Conformal verdict",
                              ["CONFIRMED", "NEEDS REVIEW (ambiguous)",
                               "FALSE POSITIVE"],
                              default=["CONFIRMED", "NEEDS REVIEW (ambiguous)"])
    with f3:
        st.markdown('<div style="height:28px"></div>', unsafe_allow_html=True)
        hz = st.toggle("🌍 Habitable-zone only")

    view = cand[(cand.p_planet >= min_p) & (cand.verdict.isin(verd))]
    if hz:
        view = view[(view.koi_teq.between(180, 310)) & (view.koi_prad <= 2.0)]
    st.markdown(f"**{len(view):,} candidates** match.")

    fig = go.Figure()
    for verdict, vcolor in [("FALSE POSITIVE", RED),
                            ("NEEDS REVIEW (ambiguous)", YELLOW),
                            ("CONFIRMED", BLUE)]:
        sub = view[view.verdict == verdict]
        if len(sub) == 0:
            continue
        fig.add_scatter(
            x=sub.koi_period, y=sub.koi_prad, mode="markers",
            name=VERDICT_STYLE[verdict][1].title(),
            marker=dict(color=vcolor, size=6, opacity=0.75),
            customdata=np.stack([sub.kepoi_name, sub.p_planet,
                                 sub.koi_teq.fillna(-1)], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b><br>p(planet)=%{customdata[1]:.3f}"
                          "<br>period %{x:.2f} d · radius %{y:.2f} R⊕"
                          "<br>T_eq %{customdata[2]:.0f} K<extra></extra>")
    fig.update_layout(**{**PLOTLY_LAYOUT,
                         "margin": dict(l=10, r=10, t=44, b=10)},
                      height=380,
                      legend=dict(orientation="h", y=1.1, x=0))
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
    st.download_button("Download this list (CSV)", table.to_csv(index=False),
                       "exojury_frontier.csv")
