"""Sky Map: Kepler's field of view in 2D and 3D."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from common import (BLUE, GRID, MUTED, PANEL, PLOTLY_LAYOUT, RED,
                    VERDICT_STYLE, YELLOW, load_artifacts, section)


def page():
    _, scores, _ = load_artifacts()

    section("Sky Map", "Kepler's field of view",
            "9,564 transit-like signals in Cygnus–Lyra (~10°×10°), observed "
            "2009–2018. Zoom the 2D view to see the telescope's 21 CCD "
            "module gaps as empty stripes; drag the 3D view to rotate.")

    mode = st.radio("View", ["2D · verdict", "2D · probability",
                             "3D · brightness depth"],
                    horizontal=True, label_visibility="collapsed")
    fig = go.Figure()
    if mode == "2D · verdict":
        for verdict, vcolor in [("FALSE POSITIVE", RED),
                                ("NEEDS REVIEW (ambiguous)", YELLOW),
                                ("NEEDS REVIEW (both plausible)", YELLOW),
                                ("CONFIRMED", BLUE)]:
            sub = scores[scores.verdict == verdict]
            if len(sub) == 0:
                continue
            fig.add_scattergl(
                x=sub.ra, y=sub.dec, mode="markers",
                name=VERDICT_STYLE[verdict][1].title(),
                marker=dict(color=vcolor, size=4, opacity=0.55),
                customdata=np.stack([sub.kepoi_name, sub.p_planet], axis=-1),
                hovertemplate="<b>%{customdata[0]}</b> · p=%{customdata[1]:.3f}"
                              "<br>RA %{x:.3f}° · Dec %{y:.3f}°<extra></extra>")
        height = 560
    elif mode == "2D · probability":
        fig.add_scattergl(
            x=scores.ra, y=scores.dec, mode="markers",
            marker=dict(color=scores.p_planet, colorscale=[
                [0, "#cde2fb"], [0.5, "#3987e5"], [1, "#0d366b"]],
                size=4, opacity=0.7,
                colorbar=dict(title="p(planet)", tickcolor=MUTED)),
            customdata=np.stack([scores.kepoi_name, scores.p_planet], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b> · p=%{customdata[1]:.3f}<extra></extra>")
        height = 560
    else:
        groups = [
            ("False Positive", scores[scores.verdict == "FALSE POSITIVE"], RED),
            ("Needs Review", scores[scores.verdict.str.startswith("NEEDS")], YELLOW),
            ("Planet", scores[scores.verdict == "CONFIRMED"], BLUE),
        ]
        for gname, sub, vcolor in groups:
            if len(sub) == 0:
                continue
            fig.add_scatter3d(
                x=sub.ra, y=sub.dec, z=sub.koi_kepmag, mode="markers",
                name=gname,
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
        height = 620
    fig.update_layout(**{**PLOTLY_LAYOUT,
                         "margin": dict(l=10, r=10, t=44, b=10)},
                      height=height,
                      legend=dict(orientation="h", y=1.06, x=0))
    if mode.startswith("2D"):
        fig.update_xaxes(title_text="right ascension [°]", autorange="reversed")
        fig.update_yaxes(title_text="declination [°]", scaleanchor="x")
    st.plotly_chart(fig, config={"displayModeBar": mode.startswith("3D")})
