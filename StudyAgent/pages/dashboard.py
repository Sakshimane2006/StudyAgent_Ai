from __future__ import annotations

from html import escape

from core.config import Settings
from database.db import get_progress_stats, list_quiz_results, list_study_plans
from components.ui import hero
import streamlit as st


def render(settings: Settings) -> None:
    hero("Your study space, powered by AI.", "A calmer way to turn your lecture notes into confident exam prep.")
    stats = get_progress_stats(settings.database_path)
    columns = st.columns(4)
    columns[0].metric("Study documents", stats["document_count"])
    columns[1].metric("Pages indexed", stats["pages"])
    columns[2].metric("Quiz attempts", stats["quiz_attempts"])
    columns[3].metric(
        "Study tasks done",
        f"{stats['tasks_completed']} / {stats['tasks_total']}",
    )

    left, right = st.columns([1.2, 0.8])
    with left:
        st.subheader("Pick up where you left off")
        st.markdown(
            '<div class="soft-card"><b>📄 My documents</b><br><span class="muted">'
            "Upload your lecture PDFs to build your private, searchable study library.</span></div>",
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            '<div class="soft-card"><b>🧠 AI study chat</b><br><span class="muted">'
            "Ask questions grounded in your own notes, with page references.</span></div>",
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            '<div class="soft-card"><b>📝 Quiz practice</b><br><span class="muted">'
            "Turn a chapter into practice questions, then track your actual results.</span></div>",
            unsafe_allow_html=True,
        )
    with right:
        st.subheader("Your next exams")
        plans = list_study_plans(settings.database_path)
        if plans:
            for plan in plans[:5]:
                st.markdown(
                    f'<div class="soft-card"><b>{escape(plan["subject"])}</b><br>'
                    f'<span class="muted">Exam date · {plan["exam_date"]} &nbsp;|&nbsp; '
                    f'{plan["hours_per_day"]:g} h/day</span></div>',
                    unsafe_allow_html=True,
                )
                st.write("")
        else:
            st.caption("Your exam plans will appear here after you add one in Study planner.")
        st.subheader("Recent quiz scores")
        results = list_quiz_results(settings.database_path, limit=4)
        if results:
            for result in results:
                percent = round(100 * result["score"] / result["total"]) if result["total"] else 0
                st.write(f"**{result['subject']}** · {result['score']}/{result['total']} ({percent}%)")
        else:
            st.caption("Complete your first quiz to see your progress here.")
