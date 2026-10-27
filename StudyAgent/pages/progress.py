from __future__ import annotations

import streamlit as st

from components.ui import hero
from core.config import Settings
from database.db import get_progress_stats, list_documents, list_quiz_results


def render(settings: Settings) -> None:
    hero("My progress", "A clear picture of the study work you have completed in StudyPilot.")
    stats = get_progress_stats(settings.database_path)
    first, second, third, fourth = st.columns(4)
    first.metric("Documents", stats["document_count"])
    second.metric("Pages indexed", stats["pages"])
    third.metric("Quiz accuracy", f"{stats['average_score']:.0f}%" if stats["average_score"] is not None else "—")
    fourth.metric("Tasks completed", f"{stats['tasks_completed']} / {stats['tasks_total']}")

    st.subheader("Quiz performance")
    st.caption(
        f"{stats['quiz_attempts']} attempts · {stats['correct_answers']} correct answers "
        f"out of {stats['quiz_questions']} questions"
    )
    history = list_quiz_results(settings.database_path, limit=30)
    if history:
        chart_rows = [
            {
                "Attempt": f"{item['subject']} · {item['completed_at']}",
                "Accuracy (%)": round(100 * item["score"] / item["total"], 1) if item["total"] else 0,
            }
            for item in reversed(history)
        ]
        st.line_chart(chart_rows, x="Attempt", y="Accuracy (%)")
        st.dataframe(
            [
                {
                    "Subject": item["subject"],
                    "Score": f"{item['score']}/{item['total']}",
                    "Difficulty": item["difficulty"],
                    "Completed": item["completed_at"],
                }
                for item in history
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Complete a quiz to see your real accuracy trend here.")

    st.subheader("Study library")
    documents = list_documents(settings.database_path)
    if documents:
        st.dataframe(
            [
                {
                    "Document": item["name"],
                    "Pages": item["page_count"],
                    "Search chunks": item["chunk_count"],
                    "Added": item["uploaded_at"],
                }
                for item in documents
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("Uploaded PDFs will be listed here after they are indexed.")
