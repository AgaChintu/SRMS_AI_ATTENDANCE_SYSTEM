
import streamlit as st
import segno
import io
import os
import html
import json
from urllib.parse import urlencode
import streamlit.components.v1 as components


@st.dialog("Share Class Link", width="small")
def share_subject_dialog(subject_name, subject_code):

    app_domain = os.getenv("APP_URL", "srms-attendance.streamlit.app").rstrip("/")
    join_url = f"{app_domain}/?{urlencode({'join-code': subject_code})}"

    safe_name = html.escape(str(subject_name))
    safe_code = html.escape(str(subject_code))

    qr = segno.make(join_url, error="h")
    qr_buffer = io.BytesIO()

    qr.save(
        qr_buffer,
        kind="png",
        scale=5,
        border=2,
        dark="#166534",
        light="#FFFFFF"
    )

    qr_buffer.seek(0)

    st.markdown("""
    <style>
    div[data-testid="stDialog"] [role="dialog"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8E5 !important;
        border-radius: 18px !important;
        padding: 16px !important;
        box-shadow: 0 12px 35px rgba(0,0,0,0.14) !important;
    }

    div[data-testid="stDialog"] h2 {
        color: #173B2A !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
    }

    div[data-testid="stDialog"] h3 {
        color: #173B2A !important;
        font-size: 0.95rem !important;
        font-weight: 650 !important;
    }

    div[data-testid="stDialog"] p {
        color: #64748B !important;
    }

    div[data-testid="stDialog"] button[aria-label="Close"] {
        color: #173B2A !important;
    }

    div[data-testid="stDialog"] input {
        background: #F1F5F2 !important;
        color: #173B2A !important;
        border: 1px solid #DCE8DF !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<div style="text-align:center;padding:0 0 12px;"><div style="font-size:23px;font-weight:750;color:#173B2A;">Scan to Join</div><div style="font-size:12px;color:#84948A;margin-top:4px;">{safe_name}</div></div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1.1, 0.9], gap="medium")

    with col1:

        st.markdown("### Copy Link")

        st.text_input(
            "Class Joining URL",
            value=join_url,
            label_visibility="collapsed",
            key=f"share_url_{subject_code}"
        )

        components.html(
            f"""
            <!DOCTYPE html>
            <html>
            <body style="margin:0;padding:0;background:transparent;">
                <div style="
                    display:flex;
                    align-items:center;
                    gap:10px;
                    width:100%;
                    box-sizing:border-box;
                    padding:2px 0;
                ">
                    <div style="
                        flex:1;
                        min-width:0;
                        background:#173B2A;
                        color:#FFFFFF;
                        padding:13px 8px;
                        border-radius:10px;
                        text-align:center;
                        font-size:18px;
                        font-weight:750;
                        letter-spacing:2px;
                        white-space:nowrap;
                        overflow:hidden;
                        text-overflow:ellipsis;
                        box-sizing:border-box;
                    ">
                        {safe_code}
                    </div>

                    <button id="copyBtn" onclick="copyCode()" style="
                        flex-shrink:0;
                        width:68px;
                        height:46px;
                        background:#B5121B;
                        color:#FFFFFF;
                        border:none;
                        border-radius:9px;
                        font-size:13px;
                        font-weight:700;
                        cursor:pointer;
                        font-family:Arial,sans-serif;
                        transition:0.2s;
                    ">
                        Copy
                    </button>
                </div>

                <script>
                async function copyCode() {{
                    const code = {json.dumps(str(subject_code))};
                    const btn = document.getElementById("copyBtn");

                    try {{
                        await navigator.clipboard.writeText(code);
                        btn.innerText = "✓ Copied";
                        btn.style.background = "#166534";
                    }} catch(error) {{
                        btn.innerText = "Failed";
                    }}
                }}
                </script>
            </body>
            </html>
            """,
            height=55,
            scrolling=False
        )

        st.markdown(
            '<div style="background:#EAF3FF;color:#315A85;padding:12px;border-radius:10px;text-align:center;font-size:12px;line-height:1.5;margin-top:8px;">Select the joining link above and press Ctrl + C to share it on WhatsApp or Email.</div>',
            unsafe_allow_html=True
        )

    with col2:

        st.markdown("### Scan to Join")

        st.image(
            qr_buffer.getvalue(),
            width=150
        )

        st.markdown(
            '<div style="text-align:center;color:#84948A;font-size:11px;margin-top:3px;">QR CODE FOR JOINING</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        '<div style="text-align:center;color:#A0AAA3;font-size:10px;margin-top:15px;letter-spacing:0.5px;">SRMS ATTENDANCE MANAGEMENT SYSTEM</div>',
        unsafe_allow_html=True
    )
