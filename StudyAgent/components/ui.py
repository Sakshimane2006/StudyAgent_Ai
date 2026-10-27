from __future__ import annotations

import streamlit as st


def hero(title: str, subtitle: str, eyebrow: str = "STUDYPILOT AI") -> None:
    st.markdown(
        f'<section class="hero"><div class="eyebrow">{eyebrow}</div>'
        f"<h1>{title}</h1><p>{subtitle}</p></section>",
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    st.info(message, icon="📘")
