from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from streamlit.testing.v1 import AppTest

from database.db import (
    add_study_task,
    create_study_plan,
    init_db,
    save_document,
    save_quiz_result,
)


def test_all_navigation_pages_render_with_saved_study_data(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "study.db"
    init_db(database)
    save_document(
        database,
        "algorithms.pdf",
        "sample-digest",
        1,
        [(1, "A queue processes items in first in, first out order.", [1.0, 0.0])],
    )
    plan_id = create_study_plan(database, "Algorithms", date.today() + timedelta(days=14), 2)
    add_study_task(database, plan_id, "Review queues", date.today() + timedelta(days=1))
    save_quiz_result(database, "Algorithms", 4, 5, "Medium")
    monkeypatch.setenv("STUDYPILOT_DB_PATH", str(database))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=20)
    assert not app.exception

    for section in (
        "My documents",
        "AI study chat",
        "Smart summaries",
        "Quiz practice",
        "Study planner",
        "My progress",
        "Dashboard",
    ):
        app.radio[0].set_value(section).run(timeout=20)
        assert not app.exception, f"{section} raised: {app.exception}"

    assert app.radio[0].value == "Dashboard"
