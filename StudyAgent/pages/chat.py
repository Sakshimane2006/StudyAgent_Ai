from __future__ import annotations

import streamlit as st

from components.ui import empty_state, hero
from core.config import Settings
from database.db import list_documents
from core.gemini import AIServiceError, GeminiService
from core.rag import answer_from_notes, retrieve_relevant_chunks


def render(settings: Settings) -> None:
    hero("Ask your notes", "A real retrieval-augmented study tutor that shows which pages informed its answer.")
    documents = list_documents(settings.database_path)
    if not documents:
        empty_state("Upload and index a text-based PDF in My documents before starting a study chat.")
        return
    choices: dict[str, int | None] = {"All documents": None}
    choices.update({f"{doc['name']} · {doc['page_count']} pages": doc["id"] for doc in documents})
    selected = st.selectbox("Search in", list(choices))
    question = st.text_area(
        "What would you like to understand?",
        placeholder="For example: Explain the difference between process and thread in simple English.",
        max_chars=2000,
    )
    if st.button("Search notes and answer", type="primary", disabled=not question.strip()):
        try:
            with st.spinner("Finding relevant passages and preparing your answer…"):
                ai = GeminiService(settings)
                sources = retrieve_relevant_chunks(
                    settings.database_path,
                    ai,
                    question,
                    document_id=choices[selected],
                )
                answer = answer_from_notes(ai, question, sources)
            st.markdown("### Study answer")
            st.write(answer)
            st.markdown("**Retrieved sources**")
            for index, source in enumerate(sources, start=1):
                st.caption(f"Source {index} · 📄 {source.document_name} · page {source.page_number}")
        except (AIServiceError, ValueError) as exc:
            st.error(str(exc))
