import streamlit as st
from pathlib import Path
import base64


def _encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def image_slider(image_paths, width=260, height=220, seconds_per_image=3.7):
    """Pure-CSS image slider.

    NOTE: The HTML is built WITHOUT blank lines or indentation on purpose.
    Streamlit renders st.markdown() through a Markdown parser, and a blank
    line (or 4+ leading spaces) would turn the <img> tags into a code block.
    """
    count = len(image_paths)
    total_time = count * seconds_per_image

    img_tags = []
    delay_rules = []
    for i, image_path in enumerate(image_paths):
        encoded = _encode_image(image_path)
        img_tags.append(
            f'<img src="data:image/png;base64,{encoded}" class="slider-img slider-{i}">'
        )
        delay_rules.append(
            f".slider-{i}{{animation-delay:{i * seconds_per_image}s;}}"
        )

    visible_end = 100 / count  # each image gets an equal slice of the cycle
    fade = min(6, visible_end / 4)

    css = (
        f".image-slider{{width:{width}px;height:{height}px;position:relative;"
        f"margin:18px auto 22px auto;overflow:hidden;border-radius:16px;"
        f"box-shadow:0 6px 18px rgba(0,0,0,0.22);background:rgba(255,255,255,0.35);}}"
        f".slider-img{{position:absolute;left:0;top:0;width:100%;height:100%;"
        f"object-fit:cover;object-position:center 25%;opacity:0;animation-name:imageChange;"
        f"animation-duration:{total_time}s;animation-iteration-count:infinite;"
        f"animation-timing-function:linear;}}"
        + "".join(delay_rules)
        + f"@keyframes imageChange{{0%{{opacity:0;}}{fade}%{{opacity:1;}}"
        f"{visible_end - fade}%{{opacity:1;}}{visible_end}%{{opacity:0;}}100%{{opacity:0;}}}}"
    )

    slider_html = (
        f"<style>{css}</style>"
        f'<div class="image-slider">{"".join(img_tags)}</div>'
    )

    st.markdown(slider_html, unsafe_allow_html=True)


def header_home():
    logo_path = (
        Path(__file__).resolve().parents[2] / "static" / "images" / "LOGO.png"
    )
    encoded_image = _encode_image(logo_path)

    st.markdown(
        '<div style="width:100%;display:flex;justify-content:center;'
        'align-items:center;margin-top:10px;">'
        f'<img src="data:image/png;base64,{encoded_image}" '
        'style="width:500px;max-width:100%;height:auto;display:block;">'
        "</div>",
        unsafe_allow_html=True,
    )


def header_dashboard():
    logo_path = (
        Path(__file__).resolve().parents[2] / "static" / "images" / "LOGO.png"
    )
    encoded_image = _encode_image(logo_path)

    st.markdown(
        '<div style="width:100%;display:flex;justify-content:center;'
        'align-items:center;margin-top:10px;">'
        f'<img src="data:image/png;base64,{encoded_image}" '
        'style="width:300px;max-width:100%;height:auto;display:block;">'
        "</div>",
        unsafe_allow_html=True,
    )


