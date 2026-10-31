import streamlit as st


def footer_home():
    st.markdown("""
        <div style="margin-top:2rem; display:flex; gap:6px; justify-content:center; align-items:center;">
            <p style="font-weight:600; color:#173B2A; font-size:13px; margin:0;">SRMS AI Attendance System • Powered by Deep Learning</p>  
        </div>
    """, unsafe_allow_html=True)


def footer_dashboard():
    st.markdown("""
        <div style="margin-top:2rem; display:flex; gap:6px; justify-content:center; align-items:center;">
            <p style="font-weight:600; color:#64748B; font-size:12px; margin:0;">SRMS • Making Attendance Faster Using AI</p>  
        </div>
    """, unsafe_allow_html=True)
