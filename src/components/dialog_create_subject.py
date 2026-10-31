
import streamlit as st
from src.database.db import create_subject


@st.dialog("Create New Subject", width="small")
def create_subject_dailog(teacher_id):

    st.markdown("""
    <style>
    div[data-testid="stDialog"] [role="dialog"] {
        background: #FFFFFF !important;
        border: none !important;
        border-radius: 22px !important;
        padding: 12px 16px !important;
        box-shadow: 0 15px 40px rgba(20, 30, 70, 0.18) !important;
    }

    div[data-testid="stDialog"] h2 {
        color: #292D3A !important;
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        text-align: left !important;
        margin-bottom: 10px !important;
    }

    div[data-testid="stDialog"] p {
        color: #555B6B !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stDialog"] label p {
        color: #34394A !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }

    div[data-testid="stDialog"] input {
        background: #F1F2F6 !important;
        color: #292D3A !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        min-height: 42px !important;
        font-size: 0.88rem !important;
        box-shadow: none !important;
    }

    div[data-testid="stDialog"] input:focus {
        background: #FFFFFF !important;
        border: 1px solid #5865F2 !important;
        box-shadow: 0 0 0 3px rgba(88,101,242,0.10) !important;
    }

    div[data-testid="stDialog"] input::placeholder {
        color: #9298A8 !important;
        opacity: 1 !important;
    }

    div[data-testid="stDialog"] div.stButton > button {
        background: #B5121B !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 30px !important;
        min-height: 45px !important;
        width: 100% !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stDialog"] div.stButton > button *,
    div[data-testid="stDialog"] div.stButton > button p {
        color: #FFFFFF !important;
    }

    div[data-testid="stDialog"] div.stButton > button:hover {
        background: #920E17 !important;
        color: #FFFFFF !important;
        box-shadow: 0 5px 14px rgba(181,18,27,0.22) !important;
        transform: translateY(-1px);
    }

    div[data-testid="stDialog"] button[aria-label="Close"] {
        color: #555B6B !important;
    }

    div[data-testid="stDialog"] button[aria-label="Close"]:hover {
        background: #F1F2F6 !important;
        color: #B5121B !important;
    }

    div[data-testid="stDialog"] [data-testid="stVerticalBlock"] {
        gap: 0.65rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        "<p style='color:#74798A;font-size:13px;margin-bottom:12px;'>Enter the details of your new subject</p>",
        unsafe_allow_html=True
    )

    sub_id = st.text_input(
        "Subject Code",
        placeholder="e.g. CS101",
        key="new_subject_code"
    )

    sub_name = st.text_input(
        "Subject Name",
        placeholder="e.g. Introduction to Programming",
        key="new_subject_name"
    )

    sub_section = st.text_input(
        "Section",
        placeholder="e.g. A",
        key="new_subject_section"
    )

    st.write("")

    if st.button(
        "Create Subject Now",
        type="primary",
        width="stretch"
    ):
        if sub_id.strip() and sub_name.strip() and sub_section.strip():

            try:
                create_subject(
                    sub_id.strip(),
                    sub_name.strip(),
                    sub_section.strip(),
                    teacher_id
                )

                st.toast("Subject Created Successfully!", icon="✅")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")

        else:
            st.warning("Please fill all the details.")


create_subject_dialog = create_subject_dailog
