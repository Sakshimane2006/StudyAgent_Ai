from __future__ import annotations

import streamlit as st

from components.ui import empty_state, hero
from core.config import Settings
from database.db import get_document_text, list_documents
from core.gemini import AIServiceError, GeminiService
from core.learning import create_study_summary


def render(settings: Settings) -> None:
    hero("Smart summaries", "Turn a chapter into revision notes, key terms, exam prompts, and flashcards.")
    documents = list_documents(settings.database_path)
    if not documents:
        empty_state("Upload a PDF in My documents before creating study material.")
        return
    documents_by_id = {document["id"]: document for document in documents}
    selected = st.selectbox(
        "Choose a chapter PDF",
        list(documents_by_id),
        format_func=lambda document_id: (
            f"{documents_by_id[document_id]['name']} · {documents_by_id[document_id]['page_count']} pages"
        ),
    )
    if selected is None:
        st.error("Choose a document before creating a study pack.")
        return
    if st.button("Create study pack", type="primary"):
        try:
            name, text, _ = get_document_text(settings.database_path, selected)
            with st.spinner("Reading your notes and creating a study pack…"):
                summary = create_study_summary(GeminiService(settings), name, text)
            st.session_state["latest_study_summary"] = summary
            st.session_state["latest_study_summary_name"] = name
            st.session_state["latest_study_summary_document_id"] = selected
        except (AIServiceError, ValueError) as exc:
            st.error(str(exc))
    summary = st.session_state.get("latest_study_summary")
    if not summary or st.session_state.get("latest_study_summary_document_id") != selected:
        return
    st.markdown(f"### Study pack · {st.session_state.get('latest_study_summary_name', '')}")
    tabs = st.tabs(["Chapter summaries", "Definitions", "Exam notes", "Flashcards"])
    with tabs[0]:
        if summary["chapter_summaries"]:
            for chapter in summary["chapter_summaries"]:
                st.markdown(f"**{chapter['title']}**")
                st.write(chapter["summary"])
        else:
            st.caption("No chapter summaries were returned for these notes.")
    with tabs[1]:
        if summary["definitions"]:
            for definition in summary["definitions"]:
                st.markdown(f"**{definition['term']}**")
                st.write(definition["definition"])
        else:
            st.caption("No definitions were identified.")
    with tabs[2]:
        if summary["exam_notes"]:
            for note in summary["exam_notes"]:
                st.markdown(f"- {note}")
        else:
            st.caption("No exam notes were identified.")
    with tabs[3]:
        if summary["flashcards"]:
            for index, card in enumerate(summary["flashcards"], start=1):
                with st.expander(f"Card {index}: {card['front']}"):
                    st.write(card["back"])
        else:
            st.caption("No flashcards were generated.")
