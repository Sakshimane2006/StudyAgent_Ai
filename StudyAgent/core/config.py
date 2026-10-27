from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _configured_value(name: str, default: str = "") -> str:
    environment_value = os.getenv(name)
    if environment_value is not None and environment_value.strip():
        return environment_value.strip()
    try:
        secret_value = st.secrets.get(name, default)
    except StreamlitSecretNotFoundError:
        return default
    return str(secret_value).strip() or default


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str
    embedding_model: str
    database_path: Path
    max_pdf_bytes: int


def get_settings() -> Settings:
    configured_database = _configured_value("STUDYPILOT_DB_PATH")
    database_path = Path(configured_database) if configured_database else ROOT_DIR / "data" / "studypilot.db"
    if not database_path.is_absolute():
        database_path = ROOT_DIR / database_path
    try:
        max_pdf_mb = int(_configured_value("MAX_PDF_MB", "20"))
    except ValueError as exc:
        raise ValueError("MAX_PDF_MB must be a whole number between 1 and 20.") from exc
    if not 1 <= max_pdf_mb <= 20:
        raise ValueError("MAX_PDF_MB must be a whole number between 1 and 20.")
    return Settings(
        api_key=_configured_value("GEMINI_API_KEY") or None,
        model=_configured_value("GEMINI_MODEL", "gemini-3.6-flash"),
        embedding_model=_configured_value("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
        database_path=database_path,
        max_pdf_bytes=max_pdf_mb * 1024 * 1024,
    )
