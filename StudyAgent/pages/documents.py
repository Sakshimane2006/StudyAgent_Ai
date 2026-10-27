from __future__ import annotations

import hashlib

import streamlit as st

from components.ui import empty_state, hero
from core.config import Settings
from database.db import delete_document, find_document_by_hash, list_documents
from core.gemini import AIServiceError, GeminiService
from core.pdf_processing import PDFProcessingError, index_pdf


def render(settings: Settings) -> None:
    hero("My documents", "Build your study library from searchable, text-based lecture PDFs.")
    st.caption(
        "PDF text and embeddings are saved in your local SQLite database. Original PDF files are not retained. "
        f"Maximum file size: {settings.max_pdf_bytes // (1024 * 1024)} MB."
    )
    uploaded_file = st.file_uploader("Choose a lecture PDF", type=["pdf"], accept_multiple_files=False)
    if uploaded_file is not None and st.button("Upload and index PDF", type="primary"):
        content = uploaded_file.getvalue()
        digest = hashlib.sha256(content).hexdigest()
        existing = find_document_by_hash(settings.database_path, digest)
        if existing:
            st.info(f"“{existing['name']}” is already in your study library.")
        else:
            try:
                with st.spinner("Extracting pages and creating private search embeddings…"):
                    index_pdf(
                        uploaded_file.name,
                        content,
                        settings,
                        GeminiService(settings),
                    )
                st.success("Your notes have been indexed and are ready for study.")
                st.rerun()
            except (PDFProcessingError, AIServiceError, ValueError) as exc:
                st.error(str(exc))

    st.subheader("Indexed library")
    documents = list_documents(settings.database_path)
    if not documents:
        empty_state("No documents yet. Upload a PDF above to start using RAG chat, summaries, and quizzes.")
        return
    for document in documents:
        with st.container(border=True):
            detail, action = st.columns([4, 1])
            with detail:
                st.markdown(f"**📄 {document['name']}**")
                st.caption(
                    f"{document['page_count']} text pages · {document['chunk_count']} indexed chunks · "
                    f"added {document['uploaded_at']}"
                )
            with action:
                if st.button("Delete", key=f"delete_doc_{document['id']}"):
                    if delete_document(settings.database_path, document["id"]):
                        if st.session_state.get("latest_study_summary_document_id") == document["id"]:
                            st.session_state.pop("latest_study_summary", None)
                            st.session_state.pop("latest_study_summary_name", None)
                            st.session_state.pop("latest_study_summary_document_id", None)
                        active_quiz = st.session_state.get("active_quiz")
                        if active_quiz and active_quiz.get("document_id") == document["id"]:
                            st.session_state.pop("active_quiz", None)
                        last_quiz = st.session_state.get("last_quiz_result")
                        if last_quiz and last_quiz.get("document_id") == document["id"]:
                            st.session_state.pop("last_quiz_result", None)
                        st.success("Document text and embeddings deleted from the local database.")
                        st.rerun()
                    st.error("This document could not be found.")
