
import streamlit as st
import time
import html

from src.database.db import enroll_student_to_subject
from src.database.config import supabase


@st.dialog("Quick Enrollment", width="small")
def enroll_dialog(subject_code):

    student_data = st.session_state.get("student_data")

    if not student_data:
        st.error("Student session expired. Please login again.")
        return

    student_id = student_data.get("student_id")
    subject_code = str(subject_code).strip()

    st.html("""
    <style>
    div[data-testid="stDialog"] [role="dialog"] {
        background: #FFFFFF !important;
        border: 1px solid #DCE8E0 !important;
        border-radius: 18px !important;
        padding: 22px !important;
        box-shadow: 0 12px 35px rgba(0,0,0,0.16) !important;
    }

    div[data-testid="stDialog"] h2 {
        color: #173B2A !important;
        font-size: 1.55rem !important;
        font-weight: 750 !important;
        margin-bottom: 18px !important;
    }

    div[data-testid="stDialog"] button[aria-label="Close"] {
        color: #173B2A !important;
    }

    div[data-testid="stDialog"] div.stButton > button {
        width: 100% !important;
        min-height: 46px !important;
        border-radius: 10px !important;
        font-weight: 650 !important;
        font-size: 14px !important;
        border: none !important;
    }

    div[data-testid="stDialog"] div.stButton > button[kind="secondary"] {
        background: #DC2626 !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stDialog"] div.stButton > button[kind="secondary"]:hover {
        background: #B91C1C !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stDialog"] div.stButton > button[kind="primary"] {
        background: #166534 !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stDialog"] div.stButton > button[kind="primary"]:hover {
        background: #14532D !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stDialog"] div.stButton button p {
        color: #FFFFFF !important;
    }
    </style>
    """)

    try:
        res = (
            supabase.table("subjects")
            .select("subject_id, name, subject_code")
            .eq("subject_code", subject_code)
            .execute()
        )

        if not res.data:
            st.error("Subject code not found.")

            if st.button("Close", width="stretch"):
                st.query_params.clear()
                st.rerun()

            return

        subject = res.data[0]

        check = (
            supabase.table("subject_students")
            .select("*")
            .eq("subject_id", subject["subject_id"])
            .eq("student_id", student_id)
            .execute()
        )

        if check.data:
            st.info("You are already enrolled in this subject.")

            if st.button("Got it!", type="primary", width="stretch"):
                st.query_params.clear()
                st.rerun()

            return

        safe_name = html.escape(str(subject["name"]))
        safe_code = html.escape(str(subject["subject_code"]))

        st.html(f"""
        <div style="text-align:center; padding:8px 0 22px;">

            <p style="
                color:#64748B;
                font-size:14px;
                margin-bottom:18px;
            ">
                You have been invited to join a class.
            </p>

            <div style="
                background:#ECFDF5;
                border:1px solid #BBF7D0;
                border-radius:12px;
                padding:18px 12px;
            ">
                <div style="
                    font-size:11px;
                    font-weight:700;
                    color:#64748B;
                    letter-spacing:1px;
                    margin-bottom:7px;
                ">
                    SUBJECT NAME
                </div>

                <div style="
                    font-size:21px;
                    font-weight:750;
                    color:#173B2A;
                ">
                    {safe_name}
                </div>

                <div style="
                    font-size:12px;
                    color:#64748B;
                    margin-top:7px;
                ">
                    Subject Code: {safe_code}
                </div>
            </div>

            <p style="
                font-size:13px;
                color:#64748B;
                margin-top:20px;
                margin-bottom:0;
            ">
                Would you like to enroll in this subject?
            </p>

        </div>
        """)

        col1, col2 = st.columns(2, gap="medium")

        with col1:
            if st.button(
                "No Thanks",
                type="secondary",
                width="stretch",
                key="quick_enroll_no"
            ):
                st.query_params.clear()
                st.rerun()

        with col2:
            if st.button(
                "Yes, Enroll Now!",
                type="primary",
                width="stretch",
                key="quick_enroll_yes"
            ):
                try:
                    enroll_student_to_subject(
                        student_id,
                        subject["subject_id"]
                    )

                    st.toast("Successfully enrolled!")
                    time.sleep(1)

                    st.query_params.clear()
                    st.rerun()

                except Exception as e:
                    st.error(f"Enrollment failed: {str(e)}")

    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")


auto_enroll_dialog = enroll_dialog
