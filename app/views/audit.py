"""The Audit: where the model disagrees with its own training labels."""

import pandas as pd
import streamlit as st

from common import LITERATURE, MUTED, load_artifacts, rgba, section


def page():
    _, scores, audit = load_artifacts()

    section("The Audit", "The model auditing its own teachers",
            "Confident learning asks: which catalog labels does an "
            "out-of-fold model most confidently disagree with? We checked "
            "the top flags against the literature after the model produced "
            "them — not before.")

    c1, c2, c3 = st.columns(3, gap="medium")
    for col, koi in [(c1, "K01450.01"), (c2, "K01416.01"), (c3, "K07016.01")]:
        tag, tcolor, note = LITERATURE[koi]
        r = scores[scores.kepoi_name == koi].iloc[0]
        name = r.kepler_name if pd.notna(r.kepler_name) else koi
        with col:
            st.markdown(f"""<div class="card">
              <span class="tag" style="background:{rgba(tcolor,.13)};color:{tcolor};">{tag}</span>
              <h4 style="margin-top:10px;">{name}
              <span style="color:{MUTED};font-weight:400;">({koi})</span></h4>
              <p>{note}</p></div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown(f"**All {len(audit)} flags** "
                f"({len(audit)/7586*100:.1f}% of labeled rows), ranked by "
                "how confidently the model disagrees:")
    st.dataframe(
        audit, width="stretch", height=430, hide_index=True,
        column_config={
            "p_planet_oof": st.column_config.ProgressColumn(
                "p(planet), out-of-fold", format="%.4f",
                min_value=0, max_value=1),
        })
    st.caption("A flag is not proof — it's a prioritised reading list. "
               "Two of the top flags were later independently demoted by "
               "NASA; one (Kepler-1520 b) is a genuinely weird real planet "
               "the model honestly gets wrong.")
