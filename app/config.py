from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    secret_key: str
    flask_host: str
    flask_port: int
    drive_folder_terminarze: str
    drive_folder_wyniki: str
    google_client_id: str
    google_client_secret: str
    google_token_path: Path
    archive_dir: Path
    root: Path


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    archive = Path(os.getenv("ARCHIVE_DIR", "data/archive"))
    if not archive.is_absolute():
        archive = ROOT / archive
    token = Path(os.getenv("GOOGLE_TOKEN_PATH", "data/secrets/google_token.json"))
    if not token.is_absolute():
        token = ROOT / token
    return Settings(
        secret_key=os.getenv("SECRET_KEY", "dev-only"),
        flask_host=os.getenv("FLASK_HOST", "127.0.0.1"),
        flask_port=int(os.getenv("FLASK_PORT", "2613")),
        drive_folder_terminarze=os.getenv(
            "DRIVE_FOLDER_TERMINARZE", "1b4fGLuJdEKdyAh6dQj-EWtnyP62Adu6a"
        ),
        drive_folder_wyniki=os.getenv(
            "DRIVE_FOLDER_WYNIKI", "1gqxtX3s6jELxpJFNev6cZwhkzycfEY7f"
        ),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        google_token_path=token,
        archive_dir=archive,
        root=ROOT,
    )
