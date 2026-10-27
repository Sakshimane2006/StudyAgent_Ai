from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from components.ui import empty_state, hero
from core.config import Settings
from database.db import (
    add_study_task,
    create_study_plan,
    delete_study_plan,
    list_study_plans,
    list_study_tasks,
    set_task_completed,
)


def render(settings: Settings) -> None:
    hero("Study planner", "Set an exam target, build a daily schedule, and save your task progress.")
    with st.form("new_study_plan"):
        subject = st.text_input("Subject or course")
        exam_date = st.date_input("Exam date", min_value=date.today(), value=date.today() + timedelta(days=14))
        hours = st.number_input("Study hours per day", min_value=0.5, max_value=16.0, value=2.0, step=0.5)
        create = st.form_submit_button("Create study plan", type="primary")
    if create:
        if not subject.strip():
            st.error("Enter a subject name to create a study plan.")
        else:
            create_study_plan(settings.database_path, subject, exam_date, hours)
            st.success(f"Study plan created for {subject.strip()}. Add your daily tasks below.")
            st.rerun()

    plans = list_study_plans(settings.database_path)
    if not plans:
        empty_state("Create your first exam plan above. Plans and task completion are saved locally.")
        return
    plans_by_id = {plan["id"]: plan for plan in plans}
    selected_plan_id = st.selectbox(
        "Plan",
        list(plans_by_id),
        format_func=lambda plan_id: (
            f"{plans_by_id[plan_id]['subject']} · exam {plans_by_id[plan_id]['exam_date']}"
        ),
    )
    selected = plans_by_id[selected_plan_id]
    task_col, delete_col = st.columns([4, 1])
    with task_col:
        with st.form(f"add_task_{selected['id']}"):
            title = st.text_input("Daily study task", placeholder="Review linked lists and solve 5 practice problems")
            due_date = st.date_input(
                "Schedule for",
                min_value=date.today(),
                max_value=date.fromisoformat(selected["exam_date"]),
                value=min(date.today(), date.fromisoformat(selected["exam_date"])),
            )
            add_task = st.form_submit_button("Add task")
        if add_task:
            if not title.strip():
                st.error("Enter a short description for the study task.")
            else:
                add_study_task(settings.database_path, selected["id"], title, due_date)
                st.rerun()
    with delete_col:
        st.write("")
        if st.button("Delete plan", key=f"delete_plan_{selected['id']}"):
            delete_study_plan(settings.database_path, selected["id"])
            st.rerun()

    tasks = list_study_tasks(settings.database_path, selected["id"])
    completed = sum(task["completed"] for task in tasks)
    if tasks:
        st.progress(completed / len(tasks), text=f"{completed} of {len(tasks)} tasks complete")
        for task in tasks:
            left, right = st.columns([5, 1])
            with left:
                st.write(f"**{task['title']}** · {task['due_date']}")
            with right:
                checked = st.checkbox(
                    "Done",
                    value=bool(task["completed"]),
                    key=f"task_done_{task['id']}",
                    label_visibility="collapsed",
                )
                if checked != bool(task["completed"]):
                    set_task_completed(settings.database_path, task["id"], checked)
                    st.rerun()
    else:
        st.caption("No tasks yet. Add your first daily study session above.")
