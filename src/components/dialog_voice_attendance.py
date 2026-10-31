import streamlit as st
import pandas as pd
from datetime import datetime
from src.pipelines.voice_pipeline import process_bulk_audio
from src.database.config import supabase
from src.components.dialog_attendance_results import show_attendance_result


@st.dialog("Voice Attendance", width="medium")
def voice_attendance_dialog(selected_subject_id):
    st.write("Record classroom audio of students speaking (e.g. saying 'I am present'). The deep voice model will automatically identify them.")

    audio_data = st.audio_input("Record classroom audio", key="dialog_voice_audio")

    if st.button("Analyze Audio", width="stretch", type="primary", icon=":material/graphic_eq:"):
        if not audio_data:
            st.warning("Please record some audio first.")
            return

        with st.spinner("Processing voice biometrics..."):
            enrolled_res = supabase.table("subject_students").select("*, students(*)").eq("subject_id", selected_subject_id).execute()
            enrolled_students = enrolled_res.data or []

            if not enrolled_students:
                st.warning("No students enrolled in this course yet.")
                return

            candidates_dict = {}
            for s in enrolled_students:
                stu = s.get("students")
                if stu and stu.get("voice_embedding"):
                    candidates_dict[stu["student_id"]] = stu["voice_embedding"]

            if not candidates_dict:
                st.error("No enrolled students have voice profiles registered yet.")
                return

            audio_bytes = audio_data.getvalue() if hasattr(audio_data, "getvalue") else audio_data.read()

            detected_scores = process_bulk_audio(audio_bytes, candidates_dict, threshold=0.65)

            results = []
            attendance_to_log = []
            current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            for node in enrolled_students:
                student = node.get("students")
                if not student:
                    continue
                sid = student["student_id"]
                score = detected_scores.get(sid, 0.0)
                is_present = bool(score > 0)

                results.append({
                    "Name": student.get("name", "Unknown"),
                    "ID": sid,
                    "Source": f"Score: {round(score, 3)}" if is_present else "—",
                    "Status": "✅ Present" if is_present else "❌ Absent"
                })

                attendance_to_log.append({
                    "student_id": sid,
                    "subject_id": selected_subject_id,
                    "timestamp": current_timestamp,
                    "is_present": bool(is_present)
                })

            st.session_state.voice_attendance_results = (pd.DataFrame(results), attendance_to_log)

    if st.session_state.get("voice_attendance_results"):
        st.divider()
        df_results, logs = st.session_state.voice_attendance_results
        show_attendance_result(df_results, logs)
