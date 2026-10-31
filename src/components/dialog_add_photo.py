import streamlit as st
from PIL import Image


@st.dialog("Capture or Upload Classroom Photos", width="medium")
def add_photos_dialog():
    st.write("Add classroom photos to scan for student attendance.")

    if "attendance_images" not in st.session_state:
        st.session_state.attendance_images = []

    if "photo_tab" not in st.session_state:
        st.session_state.photo_tab = "camera"

    t1, t2 = st.columns(2)

    with t1:
        type_camera = "primary" if st.session_state.photo_tab == "camera" else "tertiary"
        if st.button("Camera Snapshot", type=type_camera, width="stretch", icon=":material/photo_camera:"):
            st.session_state.photo_tab = "camera"
            st.rerun()

    with t2:
        type_upload = "primary" if st.session_state.photo_tab == "upload" else "tertiary"
        if st.button("Upload Photos", type=type_upload, width="stretch", icon=":material/upload_file:"):
            st.session_state.photo_tab = "upload"
            st.rerun()

    if st.session_state.photo_tab == "camera":
        cam_photo = st.camera_input("Take Snapshot", key="dialog_cam")
        if cam_photo:
            st.session_state.attendance_images.append(Image.open(cam_photo).convert("RGB"))
            st.toast("Photo Captured and Added to Gallery! 📸")
            st.rerun()

    if st.session_state.photo_tab == "upload":
        uploaded_files = st.file_uploader(
            "Choose Image Files (JPG, PNG)",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True,
            key="dialog_upload"
        )

        if uploaded_files:
            for f in uploaded_files:
                img = Image.open(f).convert("RGB")
                st.session_state.attendance_images.append(img)
            st.toast(f"{len(uploaded_files)} Photo(s) Uploaded Successfully! ✅")
            st.rerun()

    st.divider()

    st.caption(f"Currently added: {len(st.session_state.attendance_images)} photo(s).")
    if st.button("Done", type="primary", width="stretch"):
        st.rerun()
