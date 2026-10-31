import streamlit as st


def style_background_home():
    st.markdown(
        "<style>.stApp{background:#ECFDF5!important;}</style>",
        unsafe_allow_html=True,
    )


def style_background_dashboard():
    st.markdown(
        "<style>.stApp{background:#ECFDF5!important;}</style>",
        unsafe_allow_html=True,
    )


def style_base_layout():
    st.markdown(
        """<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

#MainMenu, footer, header {
    visibility: hidden;
}

.block-container {
    padding-top: 0.7rem !important;
    max-width: 1050px;
}

html, body, .stApp, .stApp * {
    font-family: 'Poppins', sans-serif;
}

.stApp [data-testid="stIconMaterial"] {
    font-family: 'Material Symbols Rounded' !important;
}

[data-testid="stColumn"] {
    display: flex;
    flex-direction: column;
}

[data-testid="stButton"], div.stButton {
    display: flex;
    justify-content: center;
    width: 100%;
}

/* Headings & general text */
h1, h2, h3, h4, h5, h6 {
    color: #173B2A !important;
}

h2 {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    color: #252B3A !important;
    margin: 0 0 0.4rem 0 !important;
    padding: 0 !important;
    letter-spacing: 0.3px;
}

.stMarkdown, .stMarkdown p, .stMarkdown span {
    color: #1E293B !important;
}

/* Widget labels (e.g. Enter username, Enter password) */
label, 
[data-testid="stWidgetLabel"], 
[data-testid="stWidgetLabel"] p, 
label p,
label span {
    color: #173B2A !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.2px;
}

/* Input boxes everywhere */
div[data-baseweb="input"],
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"] {
    background-color: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1px solid #CBD5E1 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}

div[data-baseweb="input"]:focus-within {
    border-color: #166534 !important;
    box-shadow: 0 0 0 2px rgba(22, 101, 52, 0.2) !important;
}

input, 
textarea, 
.stTextInput input, 
.stDateInput input, 
.stTimeInput input {
    background-color: #FFFFFF !important;
    color: #173B2A !important;
    -webkit-text-fill-color: #173B2A !important;
    font-size: 0.95rem !important;
}

input::placeholder, 
textarea::placeholder {
    color: #94A3B8 !important;
    -webkit-text-fill-color: #94A3B8 !important;
    opacity: 1 !important;
}

/* Selectbox styling */
div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border-radius: 10px !important;
}

div[data-baseweb="select"] * {
    color: #173B2A !important;
}

/* Home portal button sizing */
div[data-testid="stVerticalBlock"] > div > div > div.stButton > button#btn_student,
div[data-testid="stVerticalBlock"] > div > div > div.stButton > button#btn_teacher {
    width: 260px !important;
}

/* General button styling */
div.stButton > button {
    border-radius: 10px;
    padding: 10px 24px;
    font-size: 15px;
    font-weight: 600;
    transition: all 0.2s ease;
    border: none;
}

div.stButton > button[kind="primary"] {
    background-color: #166534 !important;
    color: white !important;
}

div.stButton > button[kind="primary"] * {
    color: white !important;
}

div.stButton > button[kind="primary"]:hover {
    background-color: #14532D !important;
    color: white !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(22,101,52,0.25);
}

div.stButton > button[kind="secondary"] {
    background-color: #F1F5F9 !important;
    color: #334155 !important;
    border: 1px solid #CBD5E1 !important;
}

div.stButton > button[kind="secondary"] * {
    color: #334155 !important;
}

div.stButton > button[kind="secondary"]:hover {
    background-color: #E2E8F0 !important;
    color: #0F172A !important;
    transform: translateY(-1px);
}

div.stButton > button[kind="tertiary"] {
    background-color: transparent !important;
    color: #166534 !important;
}

div.stButton > button[kind="tertiary"] * {
    color: #166534 !important;
}

div.stButton > button[kind="tertiary"]:hover {
    background-color: #E6F4EA !important;
    color: #14532D !important;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #E2EFE7;
    padding: 6px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    color: #1E293B !important;
}

.stTabs [data-baseweb="tab"] * {
    color: #1E293B !important;
}

.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #166534 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.stTabs [aria-selected="true"] * {
    color: #166534 !important;
}

/* Dialog box background */
div[data-testid="stDialog"] [role="dialog"] {
    background-color: #FFFFFF !important;
    border: 1px solid #D1E5DA !important;
    border-radius: 20px !important;
    color: #173B2A !important;
    box-shadow: 0 12px 35px rgba(0,0,0,0.18) !important;
}

div[data-testid="stDialog"] [data-testid="stVerticalBlock"] {
    background-color: transparent !important;
}

div[data-testid="stDialog"] h1,
div[data-testid="stDialog"] h2,
div[data-testid="stDialog"] h3 {
    color: #173B2A !important;
}

div[data-testid="stDialog"] label,
div[data-testid="stDialog"] p,
div[data-testid="stDialog"] span,
div[data-testid="stDialog"] [data-testid="stMarkdownContainer"] {
    color: #173B2A !important;
}

div[data-testid="stDialog"] input,
div[data-testid="stDialog"] textarea {
    background-color: #F4FAF6 !important;
    color: #173B2A !important;
    -webkit-text-fill-color: #173B2A !important;
    border: 1px solid #D1E5DA !important;
    border-radius: 10px !important;
}

div[data-testid="stDialog"] button[aria-label="Close"] {
    color: #173B2A !important;
}

/* Metrics Cards */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #D1E5DA !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04) !important;
}

[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
    font-weight: 600 !important;
    color: #64748B !important;
    font-size: 0.9rem !important;
}

[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    font-weight: 750 !important;
    color: #173B2A !important;
    font-size: 1.6rem !important;
}

/* Image slider */
.image-slider {
    margin-left: auto !important;
    margin-right: auto !important;
}

.image-slider img.slider-img {
    width: 100% !important;
    height: 100% !important;
    max-width: none !important;
    object-fit: cover !important;
    object-position: center 25% !important;
}
</style>""",
        unsafe_allow_html=True,
    )
