from __future__ import annotations

import streamlit as st

from core.config import get_settings
from database.db import init_db
from pages import chat, dashboard, documents, planner, progress, quiz, summarize

st.set_page_config(
    page_title="StudyPilot AI | Learn Smarter, Prepare Better",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink:#172554; --muted:#64748b; --blue:#4568dc; --violet:#7554d9; }
    html, body, [class*="css"] { font-family:'Segoe UI','Inter',sans-serif; }
    .stApp { background:linear-gradient(145deg,#f6f8ff 0%,#fbfaff 52%,#f7f8fc 100%); color:var(--ink); }
    h1,h2,h3 { font-family:'Segoe UI','Inter',sans-serif; color:#172554; letter-spacing:-.035em; font-weight:700; }
    [data-testid="stSidebar"] { background:linear-gradient(175deg,#101b42 0%,#212b60 65%,#392d74 100%); }
    [data-testid="stSidebar"] * { color:#f8faff; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding:.35rem .5rem; border-radius:.6rem; }
    [data-testid="stMetric"] { background:#fff; border:1px solid #e6e9f4; border-radius:16px; padding:16px 18px; box-shadow:0 6px 22px #23366c0b; }
    [data-testid="stMetricLabel"] { color:#64748b; }
    [data-testid="stMetricValue"] { color:#172554; font-family:'Segoe UI','Inter',sans-serif; }
    [data-testid="stForm"], [data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] { border-color:#e4e8f3; border-radius:16px; }
    .hero { padding:2rem 2.2rem; background:linear-gradient(115deg,#18275b 0%,#3c54b5 58%,#7255cf 100%); border-radius:22px; color:#fff; margin:.4rem 0 1.5rem; box-shadow:0 15px 40px #3b4e9a24; }
    .hero h1 { color:#fff; font-size:clamp(2rem,4vw,3rem); margin:0 0 .45rem; }
    .hero p { color:#e4e9ff; margin:.35rem 0; font-size:1.04rem; }
    .eyebrow { color:#c8d2ff; font-weight:700; font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; }
    .soft-card { background:#fff; border:1px solid #e7eaf4; border-radius:16px; padding:1.1rem 1.25rem; box-shadow:0 8px 26px #23366c08; }
    .muted { color:#64748b; }
    button[kind="primary"] { background:linear-gradient(100deg,#4568dc,#7355d6); border:0; }
    button[kind="primary"]:hover { background:linear-gradient(100deg,#395bc8,#6244c5); border:0; }
    @media (max-width:700px) { .hero { padding:1.4rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

settings = get_settings()
init_db(settings.database_path)

with st.sidebar:
    st.markdown("## 📘 StudyPilot AI")
    st.caption("Learn Smarter, Prepare Better")
    st.markdown("---")
    section = st.radio(
        "Workspace",
        [
            "Dashboard",
            "My documents",
            "AI study chat",
            "Smart summaries",
            "Quiz practice",
            "Study planner",
            "My progress",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Your notes stay on this device.")
    if settings.api_key:
        st.success(f"Gemini configured · {settings.model}", icon="🔐")
    else:
        st.warning("Add GEMINI_API_KEY to .env to enable AI features.", icon="🔑")

pages_by_name = {
    "Dashboard": dashboard,
    "My documents": documents,
    "AI study chat": chat,
    "Smart summaries": summarize,
    "Quiz practice": quiz,
    "Study planner": planner,
    "My progress": progress,
}
app_page = st.Page(
    lambda: pages_by_name[section].render(settings),
    title="StudyPilot AI",
    default=True,
)
st.navigation([app_page], position="hidden").run()
