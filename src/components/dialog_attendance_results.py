import streamlit as st
import pandas as pd
from src.database.db import create_attendance


def show_attendance_result(df, logs):
    st.write("Please review attendance results before confirming.")
    st.dataframe(df, hide_index=True, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Discard", width="stretch", type="secondary", icon=":material/delete:"):
            st.session_state.voice_attendance_results = None
            st.session_state.attendance_images = []
            st.toast("Attendance session discarded.")
            st.rerun()

    with col2:
        if st.button("Confirm & Save", width="stretch", type="primary", icon=":material/check_circle:"):
            try:
                create_attendance(logs)
                st.toast("Attendance recorded successfully! 🎉", icon="✅")
                st.session_state.attendance_images = []
                st.session_state.voice_attendance_results = None
                st.rerun()
            except Exception as e:
                st.error(f"Sync failed: {str(e)}")


@st.dialog("Attendance Review & Confirmation", width="medium")
def attendance_result_dialog(df, logs):
    show_attendance_result(df, logs)
