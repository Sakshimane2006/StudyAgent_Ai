from __future__ import annotations

import streamlit as st

from components.ui import empty_state, hero
from core.config import Settings
from database.db import get_document_text, list_documents, list_quiz_results, save_quiz_result
from core.gemini import AIServiceError, GeminiService
from core.learning import generate_quiz


def render(settings: Settings) -> None:
    hero("Quiz practice", "Generate MCQs from your notes, check your understanding, and keep a score history.")
    documents = list_documents(settings.database_path)
    if not documents:
        empty_state("Upload a PDF in My documents to create a quiz from your own notes.")
        return
    documents_by_id = {document["id"]: document for document in documents}
    with st.form("quiz_setup"):
        selected_document_id = st.selectbox(
            "Study material",
            list(documents_by_id),
            format_func=lambda document_id: (
                f"{documents_by_id[document_id]['name']} · {documents_by_id[document_id]['page_count']} pages"
            ),
        )
        selected_document = documents_by_id[selected_document_id]
        subject = st.text_input("Subject", value=selected_document["name"].removesuffix(".pdf"), max_chars=100)
        settings_row, _ = st.columns(2)
        with settings_row:
            count = st.number_input("Number of questions", min_value=1, max_value=20, value=5)
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        start_quiz = st.form_submit_button("Generate quiz", type="primary")
    if selected_document_id is None:
        st.error("Choose a study document before generating a quiz.")
        return
    if start_quiz:
        try:
            quiz_subject = (subject or "").strip()
            name, notes, _ = get_document_text(settings.database_path, selected_document_id)
            with st.spinner("Creating and validating your multiple-choice quiz…"):
                questions = generate_quiz(
                    GeminiService(settings),
                    quiz_subject or name.removesuffix(".pdf"),
                    notes,
                    int(count),
                    difficulty,
                )
            st.session_state["active_quiz"] = {
                "questions": questions,
                "subject": quiz_subject or name.removesuffix(".pdf"),
                "difficulty": difficulty,
                "document_id": selected_document_id,
            }
        except (AIServiceError, ValueError) as exc:
            st.error(str(exc))
    quiz_data = st.session_state.get("active_quiz")
    if quiz_data:
        st.markdown("### Your quiz")
        with st.form("quiz_answers"):
            answers = []
            for index, question in enumerate(quiz_data["questions"]):
                st.markdown(f"**{index + 1}. {question['question']}**")
                st.caption(f"Difficulty: {question['difficulty']}")
                answers.append(
                    st.radio(
                        f"Choose an answer for question {index + 1}",
                        range(4),
                        format_func=lambda option, options=question["options"]: options[option],
                        key=f"quiz_answer_{index}",
                        index=None,
                    )
                )
            submitted = st.form_submit_button("Submit answers", type="primary")
        if submitted:
            unanswered = [index + 1 for index, answer in enumerate(answers) if answer is None]
            if unanswered:
                st.warning(f"Please answer question(s): {', '.join(map(str, unanswered))}.")
            else:
                score = sum(
                    answer == question["correct_index"]
                    for answer, question in zip(answers, quiz_data["questions"], strict=True)
                )
                total = len(quiz_data["questions"])
                save_quiz_result(
                    settings.database_path,
                    quiz_data["subject"],
                    score,
                    total,
                    quiz_data["difficulty"],
                )
                st.session_state["last_quiz_result"] = {
                    "score": score,
                    "total": total,
                    "questions": quiz_data["questions"],
                    "answers": answers,
                    "document_id": quiz_data["document_id"],
                }
                del st.session_state["active_quiz"]
                st.rerun()
    result = st.session_state.get("last_quiz_result")
    if result:
        st.success(f"Score: {result['score']} / {result['total']} ({round(100 * result['score'] / result['total'])}%)")
        with st.expander("Review answers and explanations", expanded=True):
            for index, question in enumerate(result["questions"]):
                correct = question["correct_index"]
                st.markdown(f"**{index + 1}. {question['question']}**")
                st.write(f"Correct answer: {question['options'][correct]}")
                st.caption(question["explanation"])
    st.subheader("Quiz history")
    history = list_quiz_results(settings.database_path, limit=10)
    if history:
        st.dataframe(
            [
                {
                    "Subject": item["subject"],
                    "Score": f"{item['score']}/{item['total']}",
                    "Percent": f"{round(100 * item['score'] / item['total'])}%",
                    "Difficulty": item["difficulty"],
                    "Completed": item["completed_at"],
                }
                for item in history
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("Submitted quiz results will appear here.")
