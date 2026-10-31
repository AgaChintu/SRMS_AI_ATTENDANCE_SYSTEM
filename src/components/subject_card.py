
import streamlit as st
from textwrap import dedent
from html import escape


def subject_card(name, code, section, stats=None, footer_callback=None):

    html = f"""
<div style="
    background: #FFFFFF;
    border: 1px solid #D1E5DA;
    border-left: 7px solid #176B3A;
    padding: 26px 30px;
    border-radius: 18px;
    margin: 12px 0 18px 0;
    box-shadow: 0 4px 14px rgba(23,107,58,0.08);
    width: 100%;
    box-sizing: border-box;
">

    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 18px;
    ">
        <h3 style="
            margin: 0;
            color: #173B2A;
            font-size: 1.65rem;
            font-weight: 750;
        ">
            {escape(str(name))}
        </h3>

        <span style="
            background: #E5F4EA;
            color: #176B3A;
            padding: 7px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 700;
        ">
            SECTION {escape(str(section))}
        </span>
    </div>

    <div style="
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 22px;
    ">
        <span style="color: #64748B; font-size: 1rem;">
            Subject Code:
        </span>

        <span style="
            background: #EAF2FF;
            color: #315DB5;
            padding: 6px 13px;
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 750;
        ">
            {escape(str(code))}
        </span>
    </div>
"""

    if stats:
        html += """
<div style="
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
">
"""

        for icon, label, value in stats:
            html += f"""
<div style="
    display: flex;
    align-items: center;
    gap: 10px;
    background: #F0F8F3;
    border: 1px solid #D8EBDD;
    padding: 12px 17px;
    border-radius: 12px;
    min-width: 125px;
">
    <span style="font-size: 1.3rem;">{icon}</span>

    <div>
        <div style="
            color: #176B3A;
            font-size: 1.15rem;
            font-weight: 750;
        ">
            {escape(str(value))}
        </div>

        <div style="
            color: #64748B;
            font-size: 0.78rem;
            font-weight: 600;
        ">
            {escape(str(label))}
        </div>
    </div>
</div>
"""

        html += "</div>"

    html += "</div>"

    st.html(html)

    if footer_callback:
        footer_callback()
