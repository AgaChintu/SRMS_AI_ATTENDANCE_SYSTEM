import streamlit as st
from src.components.dailog_enroll import enroll_student_dialog


def enroll_dialog(student_id=None):
    if student_id is None:
        student_data = st.session_state.get("student_data")
        if student_data:
            student_id = student_data.get("student_id")
    enroll_student_dialog(student_id)
