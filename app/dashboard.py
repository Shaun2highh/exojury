"""ExoJury — multi-page entry point.  Run:  streamlit run app/dashboard.py"""

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR.parent / "src"))

import ui  # noqa: E402
from views import audit, frontier, home, methods, skymap, trial  # noqa: E402

st.set_page_config(page_title="ExoJury", page_icon="🪐", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(ui.CSS, unsafe_allow_html=True)

pages = st.navigation([
    st.Page(home.page, title="Home", icon="🪐", default=True),
    st.Page(trial.page, title="The Trial", icon="⚖️", url_path="trial"),
    st.Page(frontier.page, title="Frontier", icon="🚀", url_path="frontier"),
    st.Page(skymap.page, title="Sky Map", icon="🌌", url_path="sky"),
    st.Page(audit.page, title="The Audit", icon="🧾", url_path="audit"),
    st.Page(methods.page, title="Methods", icon="🧠", url_path="methods"),
], position="top")
pages.run()
