import streamlit as st
from pathlib import Path

from src.components.header import header_home, image_slider
from src.components.footer import footer_home
from src.ui.base_layout import style_background_home, style_base_layout

BASE_DIR = Path(__file__).resolve().parents[2]
IMG_DIR = BASE_DIR / "static" / "images"


def _portal_column(title, image_prefix, button_label, login_type):
    st.header(title)

    image_slider(
        [IMG_DIR / f"{image_prefix}{i}.png" for i in range(1, 5)],
        width=260,
        height=220,
    )

    if st.button(
        button_label,
        type="primary",
        icon=":material/arrow_outward:",
        key=f"btn_{login_type}",
    ):
        st.session_state["login_type"] = login_type
        st.rerun()


def home_screen():
    style_background_home()
    style_base_layout()
    header_home()

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        _portal_column("I'm Student", "student", "Student Portal", "student")

    with col2:
        _portal_column("I'm Teacher", "teacher", "Teacher Portal", "teacher")

    footer_home()
