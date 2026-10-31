import streamlit as st
import time
import html
import numpy as np
import pandas as pd
from PIL import Image
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.components.dialog_enroll import enroll_dialog
from src.pipelines.face_pipeline import (
    predict_attendance,
    get_face_embeddings,
    train_classifier
)
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import (
    get_all_students,
    get_student_by_id,
    create_student,
    get_student_subjects,
    get_student_attendance,
    unenroll_student_to_subject,
    update_student_profile
)


def student_dashboard():
    student_data = st.session_state.get("student_data")

    if not student_data:
        st.error("Student session expired. Please login again.")
        if st.button("Back to Home"):
            st.session_state["student_data"] = None
            st.session_state["login_type"] = None
            st.session_state["is_logged_in"] = False
            st.rerun()
        st.stop()

    student_id = student_data.get("student_id")
    fresh_data = get_student_by_id(student_id)
    if fresh_data:
        student_data = fresh_data
        st.session_state["student_data"] = fresh_data

    student_name = html.escape(str(student_data.get("name", "Student")))

    c1, c2 = st.columns(
        [1, 1],
        vertical_alignment="center",
        gap="large"
    )

    with c1:
        header_dashboard()

    with c2:
        st.markdown(
            f"""
            <div style="
                display:flex;
                flex-direction:column;
                justify-content:center;
                padding:10px 0;
            ">
                <div style="
                    color:#252B3A;
                    font-size:22px;
                    font-weight:700;
                    line-height:1.4;
                    margin-bottom:12px;
                ">
                    Welcome, {student_name}
                </div>
                <div style="color:#64748B;font-size:14px;font-weight:500;">
                    Student ID: <code>{student_id}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Logout",
            type="secondary",
            key="student_logout",
            width="stretch",
            shortcut="control+backspace"
        ):
            st.session_state["student_data"] = None
            st.session_state["login_type"] = None
            st.session_state["is_logged_in"] = False
            st.session_state["user_role"] = None
            st.rerun()

    st.space()

    # Load data
    try:
        with st.spinner("Loading your courses & attendance..."):
            subjects = get_student_subjects(student_id) or []
            logs = get_student_attendance(student_id) or []
    except Exception as e:
        st.error(f"Unable to load dashboard data: {str(e)}")
        return

    # Calculate overall KPIs
    stats_map = {}
    for log in logs:
        sid = log.get("subject_id")
        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0, "logs": []}
        stats_map[sid]["total"] += 1
        if log.get("is_present"):
            stats_map[sid]["attended"] += 1
        stats_map[sid]["logs"].append(log)

    total_enrolled = len(subjects)
    total_classes_all = sum(s["total"] for s in stats_map.values())
    total_attended_all = sum(s["attended"] for s in stats_map.values())
    overall_pct = round((total_attended_all / total_classes_all * 100), 1) if total_classes_all > 0 else 100.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Enrolled Subjects", total_enrolled)
    kpi2.metric("Total Classes", total_classes_all)
    kpi3.metric("Classes Attended", total_attended_all)
    kpi4.metric(
        "Overall Attendance",
        f"{overall_pct}%",
        delta="Safe" if overall_pct >= 75.0 else "Shortage Warning",
        delta_color="normal" if overall_pct >= 75.0 else "inverse"
    )

    st.markdown("---")

    dash_tab1, dash_tab2, dash_tab3 = st.tabs([
        "📚 My Enrolled Subjects",
        "📈 Detailed Attendance & 75% Tracker",
        "👤 My Biometrics Profile"
    ])

    # TAB 1: SUBJECTS
    with dash_tab1:
        col1, col2 = st.columns([1, 1], vertical_alignment="center")
        with col1:
            st.subheader("Enrolled Courses")
        with col2:
            if st.button("Enroll in Subject", type="primary", width="stretch", icon=":material/add:"):
                enroll_dialog()

        if not subjects:
            st.info("You haven't enrolled in any subjects yet. Click 'Enroll in Subject' to join your class.")
        else:
            cols = st.columns(2)
            for i, sub_node in enumerate(subjects):
                sub = sub_node.get("subjects")
                if not sub:
                    continue
                sid = sub.get("subject_id")
                stats = stats_map.get(sid, {"total": 0, "attended": 0})
                pct = round((stats["attended"] / stats["total"] * 100), 1) if stats["total"] > 0 else 0

                def unenroll_button(s_id=sid, s_name=sub.get("name")):
                    if st.button("Unenroll from this course", type="tertiary", width="stretch", icon=":material/delete_forever:", key=f"un_{s_id}"):
                        unenroll_student_to_subject(student_id, s_id)
                        st.toast(f"Unenrolled from {s_name} successfully!")
                        st.rerun()

                with cols[i % 2]:
                    subject_card(
                        name=sub.get("name", "Unknown Subject"),
                        code=sub.get("subject_code", "N/A"),
                        section=sub.get("section", "N/A"),
                        stats=[
                            ("📅", "Classes", stats["total"]),
                            ("✅", "Attended", stats["attended"]),
                            ("📊", "Attendance", f"{pct}%")
                        ],
                        footer_callback=unenroll_button
                    )

    # TAB 2: DETAILED ATTENDANCE & 75% CRITERIA TRACKER
    with dash_tab2:
        st.subheader("Attendance Compliance & Session History")
        if not subjects:
            st.info("Enroll in a subject to view attendance compliance.")
        else:
            for sub_node in subjects:
                sub = sub_node.get("subjects")
                if not sub:
                    continue
                sid = sub.get("subject_id")
                sub_stats = stats_map.get(sid, {"total": 0, "attended": 0, "logs": []})
                tot = sub_stats["total"]
                att = sub_stats["attended"]
                pct = round((att / tot * 100), 1) if tot > 0 else 0

                with st.expander(f"📘 {sub.get('name')} ({sub.get('subject_code')}) — {pct}% Attendance", expanded=True):
                    st.progress(min(1.0, pct / 100.0), text=f"Current: {pct}% (Target: 75%)")

                    p_col1, p_col2 = st.columns(2)
                    with p_col1:
                        st.write(f"• **Classes Attended:** {att} / {tot}")
                        st.write(f"• **Classes Missed:** {tot - att}")

                    with p_col2:
                        if tot == 0:
                            st.info("No classes conducted yet.")
                        elif pct >= 75.0:
                            can_miss = int(np.floor((att - 0.75 * tot) / 0.75))
                            st.success(f"✅ **Eligible for Exams!** You can afford to miss up to **{max(0, can_miss)}** more class(es) safely.")
                        else:
                            needed = int(np.ceil((0.75 * tot - att) / 0.25))
                            st.error(f"⚠️ **Attendance Shortage!** You must attend the next **{needed}** consecutive classes to attain 75% eligibility.")

                    s_logs = sub_stats.get("logs", [])
                    if s_logs:
                        st.markdown("**Session Breakdown**")
                        log_rows = []
                        for l in s_logs:
                            log_rows.append({
                                "Date & Time": l.get("timestamp"),
                                "Status": "✅ Present" if l.get("is_present") else "❌ Absent"
                            })
                        df_logs = pd.DataFrame(log_rows)
                        st.dataframe(df_logs, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No session logs recorded yet.")

    # TAB 3: BIOMETRICS PROFILE
    with dash_tab3:
        st.subheader("Biometric Enrollment Status")
        has_face = bool(student_data.get("face_embedding"))
        has_voice = bool(student_data.get("voice_embedding"))

        b_c1, b_c2 = st.columns(2)
        with b_c1:
            st.markdown(
                f"""
                <div style="padding:15px;border-radius:12px;background:#F8FAFC;border:1px solid #E2E8F0;">
                    <div style="font-size:24px;">👤</div>
                    <div style="font-weight:700;margin:6px 0;">Face Biometrics</div>
                    <div>Status: {'<span style="color:#166534;font-weight:700;">✅ Enrolled</span>' if has_face else '<span style="color:#DC2626;font-weight:700;">❌ Not Enrolled</span>'}</div>
                    <div style="font-size:12px;color:#64748B;margin-top:4px;">128-dimensional Deep Metric Embedding</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with b_c2:
            st.markdown(
                f"""
                <div style="padding:15px;border-radius:12px;background:#F8FAFC;border:1px solid #E2E8F0;">
                    <div style="font-size:24px;">🎙️</div>
                    <div style="font-weight:700;margin:6px 0;">Voice Biometrics</div>
                    <div>Status: {'<span style="color:#166534;font-weight:700;">✅ Enrolled</span>' if has_voice else '<span style="color:#DC2626;font-weight:700;">❌ Not Enrolled</span>'}</div>
                    <div style="font-size:12px;color:#64748B;margin-top:4px;">256-dimensional Speaker Embedding</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.subheader("Update / Re-enroll Biometrics")

        up_tab1, up_tab2 = st.tabs(["📸 Update Face ID", "🎙️ Update Voice ID"])

        with up_tab1:
            st.write("Capture a clear, well-lit photo of your face to update your facial recognition profile.")
            new_photo = st.camera_input("Update Face Photo", key="re_enroll_face_camera")
            if new_photo:
                if st.button("Save New Face ID", type="primary", key="btn_save_face"):
                    with st.spinner("Extracting facial embeddings..."):
                        img = np.array(Image.open(new_photo).convert("RGB"))
                        encodings = get_face_embeddings(img)
                        if encodings:
                            new_face_emb = encodings[0].tolist()
                            update_student_profile(student_id, face_embedding=new_face_emb)
                            train_classifier()
                            st.success("Face ID updated successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("No face detected in photo. Please try again.")

        with up_tab2:
            st.write("Record a 3 to 5 second audio phrase (e.g. 'My name is Somya and I am present') to enroll your voice.")
            new_voice = st.audio_input("Record Voice Sample", key="re_enroll_voice_audio")
            if new_voice:
                if st.button("Save New Voice ID", type="primary", key="btn_save_voice"):
                    with st.spinner("Extracting voice biometric embedding..."):
                        audio_val = new_voice.getvalue() if hasattr(new_voice, "getvalue") else new_voice.read()
                        v_emb = get_voice_embedding(audio_val)
                        if v_emb:
                            update_student_profile(student_id, voice_embedding=v_emb)
                            st.success("Voice ID enrolled successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to extract voice embedding. Please try speaking clearly.")

    footer_dashboard()


def student_screen():
    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state and st.session_state["student_data"]:
        student_dashboard()
        return

    if "student_login_type" not in st.session_state:
        st.session_state["student_login_type"] = "login"

    if st.session_state["student_login_type"] == "login":
        student_screen_login()
    else:
        student_screen_register()


def student_screen_login():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type="secondary", key="student_login_back", shortcut="control+backspace"):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Student Login (Face ID)", text_alignment="center")
    st.write("Look directly into the camera to scan your face and log in.")

    all_students = get_all_students() or []

    if not all_students:
        st.info("👋 Welcome! There are no registered students in the system yet. Please register your student profile below to get started!")
        if st.button("Register New Student Profile", type="primary", width="stretch", icon=":material/person_add:"):
            st.session_state["student_login_type"] = "register"
            st.rerun()
        footer_dashboard()
        return

    photo_source = st.camera_input("Center your face in front of the camera", key="student_login_cam")

    if photo_source:
        img = np.array(Image.open(photo_source).convert("RGB"))

        with st.spinner("AI is verifying your face..."):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.warning("No face detected in camera! Please make sure your face is clearly visible and centered.")
            elif num_faces > 1:
                st.warning("Multiple faces detected! Please scan individually.")
            else:
                if detected:
                    student_id = list(detected.keys())[0]
                    student = next((s for s in all_students if s.get("student_id") == student_id), None)

                    if student:
                        st.session_state["is_logged_in"] = True
                        st.session_state["user_role"] = "student"
                        st.session_state["student_data"] = student
                        st.toast(f"Welcome back, {student.get('name', 'Student')}! 👋")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Student ID matched but record not found in database.")
                else:
                    st.error("Face not recognized in registered students database!")
                    st.info("Are you a new student? Click 'Register New Profile' below.")

    st.markdown("---")
    col_reg1, col_reg2 = st.columns(2)
    with col_reg1:
        if st.button("New Student? Register Now", type="primary", width="stretch", icon=":material/person_add:"):
            st.session_state["student_login_type"] = "register"
            st.rerun()

    with col_reg2:
        # Fallback profile picker if camera is blocked/unavailable
        with st.popover("Quick Login (No Camera)"):
            student_dict = {f"{s.get('name')} (ID: {s.get('student_id')})": s for s in all_students}
            chosen_label = st.selectbox("Select Your Profile", list(student_dict.keys()), key="pop_stu_sel")
            if st.button("Login Selected", key="pop_stu_btn", type="primary", width="stretch"):
                chosen_student = student_dict[chosen_label]
                st.session_state["is_logged_in"] = True
                st.session_state["user_role"] = "student"
                st.session_state["student_data"] = chosen_student
                st.toast(f"Welcome back {chosen_student.get('name')}!")
                time.sleep(1)
                st.rerun()

    footer_dashboard()


def student_screen_register():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Login", type="secondary", key="student_reg_back", shortcut="control+backspace"):
            st.session_state["student_login_type"] = "login"
            st.rerun()

    st.header("Register New Student Profile", text_alignment="center")
    st.write("Enter your details and capture your face to enroll in the AI attendance system.")

    new_name = st.text_input("Full Name", placeholder="E.g. Somya Agarwal", key="reg_name_input")

    st.subheader("1. Face Biometric Enrollment")
    st.caption("A clear photo of your face is required for Face ID attendance.")
    reg_photo = st.camera_input("Capture Face Photo", key="student_reg_face_cam")

    st.subheader("2. Voice Enrollment (Optional)")
    st.caption("Record a 3-second sample (e.g. 'I am present') for voice attendance.")
    audio_data = st.audio_input("Record Voice Sample", key="student_reg_voice_mic")

    st.markdown("---")

    btn1, btn2 = st.columns(2)

    with btn1:
        if st.button("Complete Registration & Login", type="primary", width="stretch", icon=":material/how_to_reg:"):
            if not new_name.strip():
                st.warning("Please enter your full name.")
            elif not reg_photo:
                st.warning("Please capture your face photo using the camera above.")
            else:
                with st.spinner("Analyzing face biometrics & saving profile..."):
                    img = np.array(Image.open(reg_photo).convert("RGB"))
                    encodings = get_face_embeddings(img)

                    if not encodings:
                        st.error("No face detected in the captured photo! Please face the camera with good lighting and retake.")
                    else:
                        face_emb = encodings[0].tolist()
                        voice_emb = None
                        if audio_data:
                            audio_val = audio_data.getvalue() if hasattr(audio_data, "getvalue") else audio_data.read()
                            voice_emb = get_voice_embedding(audio_val)

                        try:
                            response_data = create_student(
                                new_name=new_name.strip(),
                                face_embedding=face_emb,
                                voice_embedding=voice_emb
                            )

                            if response_data:
                                train_classifier()
                                new_student = response_data[0]
                                st.session_state["is_logged_in"] = True
                                st.session_state["user_role"] = "student"
                                st.session_state["student_data"] = new_student
                                st.toast(f"Account created! Welcome, {new_name.strip()}! 🎉", icon="✅")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("Database failed to insert student profile.")
                        except Exception as e:
                            st.error(f"Registration error: {str(e)}")

    with btn2:
        if st.button("Already Registered? Login Instead", type="secondary", width="stretch", icon=":material/login:"):
            st.session_state["student_login_type"] = "login"
            st.rerun()

    footer_dashboard()
