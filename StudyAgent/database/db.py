"""SQLite persistence layer for StudyPilot AI."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Generator


@contextmanager
def get_connection(database_path: Path) -> Generator[sqlite3.Connection, None, None]:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _inserted_id(cursor: sqlite3.Cursor) -> int:
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite did not return the ID for a newly created record.")
    return cursor.lastrowid


def init_db(database_path: Path) -> None:
    with get_connection(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sha256 TEXT NOT NULL UNIQUE,
                page_count INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                UNIQUE(document_id, chunk_index)
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                difficulty TEXT NOT NULL,
                completed_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                hours_per_day REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS study_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                due_date TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_plan_date ON study_tasks(plan_id, due_date);
            """
        )


def find_document_by_hash(database_path: Path, sha256: str) -> sqlite3.Row | None:
    with get_connection(database_path) as connection:
        return connection.execute("SELECT id, name FROM documents WHERE sha256 = ?", (sha256,)).fetchone()


def save_document(
    database_path: Path,
    name: str,
    sha256: str,
    page_count: int,
    chunks: list[tuple[int, str, list[float]]],
) -> int:
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO documents (name, sha256, page_count) VALUES (?, ?, ?)",
            (name, sha256, page_count),
        )
        document_id = _inserted_id(cursor)
        connection.executemany(
            """INSERT INTO document_chunks
               (document_id, chunk_index, page_number, content, embedding_json)
               VALUES (?, ?, ?, ?, ?)""",
            [
                (document_id, index, page_number, content, json.dumps(vector))
                for index, (page_number, content, vector) in enumerate(chunks)
            ],
        )
    return document_id


def list_documents(database_path: Path) -> list[sqlite3.Row]:
    with get_connection(database_path) as connection:
        return connection.execute(
            """SELECT d.id, d.name, d.page_count, d.uploaded_at, COUNT(c.id) AS chunk_count
               FROM documents d LEFT JOIN document_chunks c ON c.document_id = d.id
               GROUP BY d.id ORDER BY d.uploaded_at DESC, d.id DESC"""
        ).fetchall()


def delete_document(database_path: Path, document_id: int) -> bool:
    with get_connection(database_path) as connection:
        cursor = connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return cursor.rowcount > 0


def fetch_document_chunks(database_path: Path, document_id: int | None = None) -> list[sqlite3.Row]:
    query = """SELECT c.page_number, c.content, c.embedding_json, d.name
               FROM document_chunks c JOIN documents d ON d.id = c.document_id"""
    params: tuple[int, ...] = ()
    if document_id is not None:
        query += " WHERE d.id = ?"
        params = (document_id,)
    query += " ORDER BY d.id, c.chunk_index"
    with get_connection(database_path) as connection:
        return connection.execute(query, params).fetchall()


def get_document_text(database_path: Path, document_id: int) -> tuple[str, str, int]:
    with get_connection(database_path) as connection:
        document = connection.execute(
            "SELECT name, page_count FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        if document is None:
            raise ValueError("The selected document no longer exists.")
        chunks = connection.execute(
            "SELECT content FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
            (document_id,),
        ).fetchall()
    return document["name"], "\n\n".join(row["content"] for row in chunks), document["page_count"]


def save_quiz_result(database_path: Path, subject: str, score: int, total: int, difficulty: str) -> None:
    with get_connection(database_path) as connection:
        connection.execute(
            "INSERT INTO quiz_results (subject, score, total, difficulty) VALUES (?, ?, ?, ?)",
            (subject.strip(), score, total, difficulty),
        )


def list_quiz_results(database_path: Path, limit: int = 10) -> list[sqlite3.Row]:
    with get_connection(database_path) as connection:
        return connection.execute(
            """SELECT id, subject, score, total, difficulty, completed_at
               FROM quiz_results ORDER BY completed_at DESC, id DESC LIMIT ?""",
            (limit,),
        ).fetchall()


def create_study_plan(database_path: Path, subject: str, exam_date: date, hours_per_day: float) -> int:
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO study_plans (subject, exam_date, hours_per_day) VALUES (?, ?, ?)",
            (subject.strip(), exam_date.isoformat(), hours_per_day),
        )
        return _inserted_id(cursor)


def list_study_plans(database_path: Path) -> list[sqlite3.Row]:
    with get_connection(database_path) as connection:
        return connection.execute(
            "SELECT id, subject, exam_date, hours_per_day FROM study_plans ORDER BY exam_date, id"
        ).fetchall()


def add_study_task(database_path: Path, plan_id: int, title: str, due_date: date) -> int:
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO study_tasks (plan_id, title, due_date) VALUES (?, ?, ?)",
            (plan_id, title.strip(), due_date.isoformat()),
        )
        return _inserted_id(cursor)


def list_study_tasks(database_path: Path, plan_id: int) -> list[sqlite3.Row]:
    with get_connection(database_path) as connection:
        return connection.execute(
            """SELECT id, title, due_date, completed
               FROM study_tasks WHERE plan_id = ? ORDER BY due_date, id""",
            (plan_id,),
        ).fetchall()


def set_task_completed(database_path: Path, task_id: int, completed: bool) -> None:
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "UPDATE study_tasks SET completed = ? WHERE id = ?", (int(completed), task_id)
        )
        if cursor.rowcount == 0:
            raise ValueError("This study task no longer exists.")


def delete_study_plan(database_path: Path, plan_id: int) -> bool:
    with get_connection(database_path) as connection:
        cursor = connection.execute("DELETE FROM study_plans WHERE id = ?", (plan_id,))
        return cursor.rowcount > 0


def get_progress_stats(database_path: Path) -> dict[str, Any]:
    with get_connection(database_path) as connection:
        document = connection.execute(
            "SELECT COUNT(*) AS document_count, COALESCE(SUM(page_count), 0) AS pages FROM documents"
        ).fetchone()
        quiz = connection.execute(
            "SELECT COUNT(*) AS attempts, COALESCE(SUM(score), 0) AS correct, "
            "COALESCE(SUM(total), 0) AS questions, AVG(100.0 * score / NULLIF(total, 0)) AS average "
            "FROM quiz_results"
        ).fetchone()
        tasks = connection.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(completed), 0) AS completed FROM study_tasks"
        ).fetchone()
        return {
            "document_count": document["document_count"],
            "pages": document["pages"],
            "quiz_attempts": quiz["attempts"],
            "correct_answers": quiz["correct"],
            "quiz_questions": quiz["questions"],
            "average_score": quiz["average"],
            "tasks_total": tasks["total"],
            "tasks_completed": tasks["completed"],
        }
