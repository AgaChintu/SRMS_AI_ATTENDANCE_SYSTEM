import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.database.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_teacher_subjects,
    get_attendance_for_teacher,
    delete_subject,
    delete_attendance_session,
    get_enrolled_students,
    get_all_students,
    enroll_student_to_subject,
    unenroll_student_to_subject
)
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog
from src.pipelines.face_pipeline import predict_attendance
from src.components.dialog_attendance_results import attendance_result_dialog
from src.components.dialog_voice_attendance import voice_attendance_dialog
from src.database.config import supabase


def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif "teacher_login_type" not in st.session_state or st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, {teacher_data.get('name', 'Teacher')}")
        if st.button("Logout", type="secondary", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state["is_logged_in"] = False
            del st.session_state.teacher_data
            st.rerun()

    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"

    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == "take_attendance" else "tertiary"
        if st.button("Take Attendance", type=type1, width="stretch", icon=":material/ar_on_you:"):
            st.session_state.current_teacher_tab = "take_attendance"
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == "manage_subjects" else "tertiary"
        if st.button("Manage Subjects", type=type2, width="stretch", icon=":material/book_ribbon:"):
            st.session_state.current_teacher_tab = "manage_subjects"
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == "attendance_records" else "tertiary"
        if st.button("Attendance Records", type=type3, width="stretch", icon=":material/cards_stack:"):
            st.session_state.current_teacher_tab = "attendance_records"
            st.rerun()

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    elif st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    elif st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    footer_dashboard()


def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data["teacher_id"]
    st.header("Take AI Attendance")

    if "attendance_images" not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning("You haven't created any subjects yet! Please create one to begin!")
        return

    subject_options = {f"{s['name']} - {s['subject_code']}": s["subject_id"] for s in subjects}

    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")

    with col1:
        selected_subject_label = st.selectbox("Select Subject", options=list(subject_options.keys()))

    with col2:
        if st.button("Add Photos", type="primary", icon=":material/photo_prints:", width="stretch"):
            add_photos_dialog()

    selected_subject_id = subject_options[selected_subject_label]

    st.divider()

    if st.session_state.attendance_images:
        st.header("Added Photos")
        gallery_cols = st.columns(4)

        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, use_container_width=True, caption=f"Photo {idx + 1}")

    has_photos = bool(st.session_state.attendance_images)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Clear all photos", width="stretch", type="tertiary", icon=":material/delete:", disabled=not has_photos):
            st.session_state.attendance_images = []
            st.rerun()

    with c2:
        if st.button("Run Face Analysis", width="stretch", type="secondary", icon=":material/analytics:", disabled=not has_photos):
            with st.spinner("Deep scanning classroom photos..."):
                all_detected_ids = {}

                for idx, img in enumerate(st.session_state.attendance_images):
                    img_np = np.array(img.convert("RGB"))
                    detected, _, _ = predict_attendance(img_np)

                    if detected:
                        for sid in detected.keys():
                            student_id = int(sid)
                            all_detected_ids.setdefault(student_id, []).append(f"Photo {idx + 1}")

                enrolled_res = supabase.table("subject_students").select("*, students(*)").eq("subject_id", selected_subject_id).execute()
                enrolled_students = enrolled_res.data or []

                if not enrolled_students:
                    st.warning("No students enrolled in this course yet.")
                else:
                    results = []
                    attendance_to_log = []
                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                    for node in enrolled_students:
                        student = node.get("students")
                        if not student:
                            continue
                        sid = int(student["student_id"])
                        sources = all_detected_ids.get(sid, [])
                        is_present = len(sources) > 0

                        results.append({
                            "Name": student.get("name", "Unknown"),
                            "ID": sid,
                            "Source": ", ".join(sources) if is_present else "—",
                            "Status": "✅ Present" if is_present else "❌ Absent"
                        })

                        attendance_to_log.append({
                            "student_id": sid,
                            "subject_id": selected_subject_id,
                            "timestamp": current_timestamp,
                            "is_present": bool(is_present)
                        })

                    attendance_result_dialog(pd.DataFrame(results), attendance_to_log)

    with c3:
        if st.button("Use Voice Attendance", type="primary", width="stretch", icon=":material/mic:"):
            voice_attendance_dialog(selected_subject_id)


def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data["teacher_id"]
    col1, col2 = st.columns(2, vertical_alignment="center")

    with col1:
        st.header("Manage Subjects")

    with col2:
        if st.button("Create New Subject", width="stretch", icon=":material/add:"):
            create_subject_dialog(teacher_id)

    st.divider()

    subjects = get_teacher_subjects(teacher_id)

    if subjects:
        cols = st.columns(2)
        for i, sub in enumerate(subjects):
            stats = [
                ("🫂", "Students", sub.get("total_students", 0)),
                ("🕰️", "Classes", sub.get("total_classes", 0)),
            ]

            def share_btn(s=sub):
                if st.button(f"Share Code: {s['name']}", key=f"share_{s['subject_code']}", icon=":material/share:", width="stretch"):
                    share_subject_dialog(s["name"], s["subject_code"])

            with cols[i % 2]:
                subject_card(
                    name=sub["name"],
                    code=sub["subject_code"],
                    section=sub["section"],
                    stats=stats,
                    footer_callback=share_btn
                )

                # Roster view & options expander
                sub_id = sub["subject_id"]
                with st.expander(f"📋 Roster: {sub['name']} ({sub['subject_code']})"):
                    enrolled = get_enrolled_students(sub_id)
                    st.write(f"**Enrolled Students ({len(enrolled)})**")

                    if enrolled:
                        for s in enrolled:
                            es1, es2, es3 = st.columns([2.5, 1.5, 1], vertical_alignment="center")
                            with es1:
                                st.write(f"• **{s.get('name', 'Student')}** (ID: {s.get('student_id')})")
                            with es2:
                                face_badge = "👤 Face" if s.get("face_embedding") else "—"
                                voice_badge = "🎤 Voice" if s.get("voice_embedding") else "—"
                                st.caption(f"{face_badge} | {voice_badge}")
                            with es3:
                                if st.button("Remove", key=f"rem_stu_{sub_id}_{s.get('student_id')}", type="tertiary"):
                                    unenroll_student_to_subject(s.get("student_id"), sub_id)
                                    st.toast(f"Removed {s.get('name')}")
                                    st.rerun()
                    else:
                        st.info("No students enrolled yet.")

                    st.markdown("---")
                    st.markdown("**Add Student to Class**")
                    all_students = get_all_students() or []
                    enrolled_ids = {s.get("student_id") for s in enrolled}
                    available = [s for s in all_students if s.get("student_id") not in enrolled_ids]

                    if available:
                        student_opts = {f"{s.get('name')} (ID: {s.get('student_id')})": s.get("student_id") for s in available}
                        chosen = st.selectbox("Select Student", list(student_opts.keys()), key=f"sel_add_{sub_id}")
                        if st.button("Enroll Student", key=f"btn_add_{sub_id}", icon=":material/person_add:"):
                            enroll_student_to_subject(student_opts[chosen], sub_id)
                            st.toast("Student enrolled successfully!")
                            st.rerun()

                    st.markdown("---")
                    if st.checkbox("Confirm Delete Subject", key=f"chk_del_{sub_id}"):
                        if st.button("Delete Subject", type="secondary", key=f"del_sub_btn_{sub_id}"):
                            ok, _ = delete_subject(sub_id)
                            if ok:
                                st.toast("Subject deleted.")
                                st.rerun()
                            else:
                                st.error("Failed to delete subject.")
    else:
        st.info("No subjects found. Create one above.")


def teacher_tab_attendance_records():
    st.header("Attendance Records")

    teacher_id = st.session_state.teacher_data["teacher_id"]
    records = get_attendance_for_teacher(teacher_id)

    if not records:
        st.info("No attendance sessions recorded yet.")
        return

    data = []
    for r in records:
        ts = r.get("timestamp")
        parsed_time = "N/A"
        if ts:
            try:
                parsed_time = datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p")
            except Exception:
                parsed_time = str(ts)

        data.append({
            "ts_group": ts.split(".")[0] if ts else None,
            "raw_ts": ts,
            "Time": parsed_time,
            "Subject": r.get("subjects", {}).get("name", "Unknown"),
            "Subject Code": r.get("subjects", {}).get("subject_code", "N/A"),
            "is_present": bool(r.get("is_present", False)),
            "student_id": r.get("student_id")
        })

    df = pd.DataFrame(data)

    summary = (
        df.groupby(["ts_group", "Time", "Subject", "Subject Code"])
        .agg(
            Present_Count=("is_present", "sum"),
            Total_Count=("is_present", "count")
        )
        .reset_index()
    )

    summary["Attendance Stats"] = (
        "✅ " + summary["Present_Count"].astype(str) + " / "
        + summary["Total_Count"].astype(str) + " Students"
    )

    display_df = (
        summary.sort_values(by="ts_group", ascending=False)
        [["Time", "Subject", "Subject Code", "Attendance Stats"]]
    )

    st.subheader("Historical Sessions Summary")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Detailed analytics and export
    st.markdown("---")
    r_tab1, r_tab2 = st.tabs(["📊 Student Compliance & Defaulters", "📥 Download Reports"])

    with r_tab1:
        st.subheader("Student Attendance Compliance")
        # Group by student and subject
        all_students = get_all_students() or []
        student_name_map = {s.get("student_id"): s.get("name") for s in all_students}

        stu_summary = (
            df.groupby(["student_id", "Subject", "Subject Code"])
            .agg(
                Attended=("is_present", "sum"),
                Total_Classes=("is_present", "count")
            )
            .reset_index()
        )
        stu_summary["Student Name"] = stu_summary["student_id"].map(student_name_map).fillna("Student")
        stu_summary["Percentage"] = (stu_summary["Attended"] / stu_summary["Total_Classes"] * 100).round(1).astype(str) + "%"
        stu_summary["Status"] = np.where(
            stu_summary["Attended"] / stu_summary["Total_Classes"] >= 0.75,
            "✅ Eligible",
            "⚠️ Shortage (<75%)"
        )

        display_compliance = stu_summary[["Student Name", "Subject", "Subject Code", "Attended", "Total_Classes", "Percentage", "Status"]]
        st.dataframe(display_compliance, use_container_width=True, hide_index=True)

    with r_tab2:
        st.subheader("Export Attendance Data")
        csv_full = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download All Attendance Logs (CSV)",
            data=csv_full,
            file_name=f"teacher_{teacher_id}_attendance_logs.csv",
            mime="text/csv",
            type="primary"
        )


def login_teacher(username, password):
    if not username or not password:
        return False

    teacher = teacher_login(username, password)
    if teacher:
        st.session_state.user_role = "teacher"
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True

    return False


def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type="secondary", key="loginbackbtn"):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Login using password")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    teacher_username = st.text_input("Enter username", placeholder="anany@521")
    teacher_pass = st.text_input("Enter password", type="password", placeholder="Enter password")

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button("Login", icon=":material/passkey:", shortcut="control+enter", width="stretch"):
            if login_teacher(teacher_username, teacher_pass):
                st.toast("Welcome back!", icon="👋")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username and password combination.")

    with btnc2:
        if st.button("Register Instead", type="primary", icon=":material/passkey:", width="stretch"):
            st.session_state.teacher_login_type = "register"
            st.rerun()

    footer_dashboard()


def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if not teacher_username or not teacher_name or not teacher_pass:
        return False, "All Fields are required!"
    if check_teacher_exists(teacher_username):
        return False, "Username already taken"
    if teacher_pass != teacher_pass_confirm:
        return False, "Passwords do not match"

    try:
        create_teacher(teacher_username, teacher_pass, teacher_name)
        return True, "Successfully created! Please login now."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type="secondary", key="loginbackbtn", shortcut="control+backspace"):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Register your teacher profile", text_alignment="center")
    st.space()
    st.space()
    
    teacher_username = st.text_input("Enter username", placeholder="anany@545")
    teacher_name = st.text_input("Enter name", placeholder="Ananya Roy")
    teacher_pass = st.text_input("Enter password", type="password", placeholder="Enter password")
    teacher_pass_confirm = st.text_input("Confirm your password", type="password", placeholder="Confirm password")

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button("Register now", icon=":material/passkey:", shortcut="control+enter", width="stretch"):
            success, message = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)
            if success:
                st.success(message)
                import time
                time.sleep(2)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)

    with btnc2:
        if st.button("Login Instead", type="primary", icon=":material/passkey:", width="stretch"):
            st.session_state.teacher_login_type = "login"
            st.rerun()

    footer_dashboard()
