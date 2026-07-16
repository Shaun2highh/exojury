"""Landing page: what ExoJury is, why it exists, what it found."""

import streamlit as st

import ui
from common import BLUE, RED, VIOLET, YELLOW, load_artifacts, rgba, section


def page():
    st.iframe(ui.landing_hero_html(), height=430)

    st.markdown(ui.stat_row([
        ("9,564", "Kepler objects on trial"),
        ("98.2%", "honest test accuracy"),
        ("95.6%", "conformal coverage (target 95%)"),
        ("2", "NASA-verified catalog errors found"),
        ("1,978", "unresolved candidates ranked"),
    ]), unsafe_allow_html=True)

    section("The problem", "Most models on this dataset cheat without knowing it",
            "NASA's KOI table quietly contains its own answer key — columns "
            "written by the vetting process itself. Two lines of code using "
            "them score 99.96% with zero machine learning.")
    c1, c2, c3 = st.columns(3, gap="medium")
    cards = [
        ("01 — Audit", "Every one of the 140 columns is assigned to a "
         "documented leakage tier. Everything the vetting pipeline wrote — "
         "names, dispositions, comments, Robovetter flags — is excluded. "
         "What's left is physics."),
        ("02 — Judge", "A gradient-boosted model returns a calibrated "
         "probability, and conformal prediction wraps it in a 95% "
         "statistical guarantee. When evidence is ambiguous, ExoJury "
         "abstains and says NEEDS REVIEW."),
        ("03 — Appeal", "The model then audits its own training labels. "
         "Its top disagreements include two 'confirmed planets' that NASA "
         "itself later demoted — rediscovered from this CSV alone."),
    ]
    for col, (title, body) in zip((c1, c2, c3), cards):
        with col:
            st.markdown(f'<div class="card"><h4>{title}</h4><p>{body}</p></div>',
                        unsafe_allow_html=True)

    section("The headline result", "It found real errors in NASA's catalog",
            "Checked against the literature only after the model flagged them.")
    r1, r2, r3 = st.columns(3, gap="medium")
    finds = [
        ("Kepler-854 b", RED, "Verified catch",
         "Snapshot says CONFIRMED · ExoJury says p = 0.00003 · NASA demoted "
         "it to false positive in 2022."),
        ("Kepler-840 b", RED, "Verified catch",
         "Snapshot says CONFIRMED · ExoJury says p = 0.0016 · also demoted "
         "by NASA after the same mass revision."),
        ("Kepler-452 b", YELLOW, "Disputed",
         "'Earth's cousin' · ExoJury says p = 0.0006 · its statistical "
         "validation is formally disputed in the literature."),
    ]
    for col, (name, color, tag, body) in zip((r1, r2, r3), finds):
        with col:
            st.markdown(
                f'<div class="card">'
                f'<span class="tag" style="background:{rgba(color,.13)};color:{color};">{tag}</span>'
                f'<h4 style="margin-top:10px;">{name}</h4><p>{body}</p></div>',
                unsafe_allow_html=True)

    section("Explore", "Six views into the pipeline",
            "Use the navigation above — every page runs live on the real data.")
    g1, g2, g3 = st.columns(3, gap="medium")
    guide = [
        ("⚖️ The Trial", "Put any of the 9,564 objects on trial: 3D system "
         "view, calibrated verdict, evidence, and an AI-written dossier."),
        ("🚀 Frontier", "The 1,978 candidates nobody has resolved yet, "
         "ranked for telescope follow-up. Includes a habitable-zone filter."),
        ("🌌 Sky Map", "All objects in Kepler's real field of view — 2D and "
         "rotatable 3D."),
        ("🧾 The Audit", "Where the model disagrees with its own teachers, "
         "with literature receipts."),
        ("📏 Honesty", "Calibration curves, coverage tests, and exactly how "
         "much accuracy the leakage was worth."),
        ("🧠 Methods", "The full pipeline, a plain-language glossary, and "
         "our honest limitations."),
    ]
    for i, (title, body) in enumerate(guide):
        with (g1, g2, g3)[i % 3]:
            st.markdown(f'<div class="card" style="margin-bottom:12px;">'
                        f'<h4>{title}</h4><p>{body}</p></div>',
                        unsafe_allow_html=True)

    st.markdown(
        '<p style="color:#565b63;font-size:12.5px;margin-top:26px;">'
        "Data: NASA Exoplanet Archive · KOI cumulative table (DOI 10.26133/NEA4) "
        "· NASA Exoplanet Science Institute, IPAC/Caltech · Challenge by Celesta "
        "· AI dossiers via Featherless.ai</p>", unsafe_allow_html=True)
