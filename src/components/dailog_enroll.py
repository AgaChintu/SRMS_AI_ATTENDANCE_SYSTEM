
import streamlit as st
import time
from src.database.db import supabase, enroll_student_to_subject


@st.dialog("Enroll in Subject", width="small")
def enroll_student_dialog(student_id):

    st.markdown(
        """
        <div style="color:#64748B;font-size:14px;margin-bottom:18px;">
            Enter the subject code provided by your teacher to join the class.
        </div>
        """,
        unsafe_allow_html=True
    )

    join_code = st.text_input(
        "Subject Code",
        placeholder="e.g. BCS301",
        max_chars=20
    )

    if st.button(
        "Enroll Now",
        type="primary",
        width="stretch"
    ):
        if not join_code.strip():
            st.warning("Please enter a subject code.")

        else:
            try:
                code = join_code.strip().upper()

                with st.spinner("Verifying subject code..."):

                    res = (
                        supabase.table("subjects")
                        .select("subject_id, name, subject_code")
                        .eq("subject_code", code)
                        .execute()
                    )

                    if not res.data:
                        st.error("Invalid subject code. Please check again.")

                    else:
                        subject = res.data[0]

                        check = (
                            supabase.table("subject_students")
                            .select("*")
                            .eq("subject_id", subject["subject_id"])
                            .eq("student_id", student_id)
                            .execute()
                        )

                        if check.data:
                            st.warning("You are already enrolled in this subject.")

                        else:
                            enroll_student_to_subject(
                                student_id,
                                subject["subject_id"]
                            )

                            st.success(
                                f"Successfully enrolled in {subject['name']}!"
                            )

                            time.sleep(1)
                            st.rerun()

            except Exception as e:
                st.error(f"Enrollment failed: {str(e)}")
