from __future__ import annotations

from datetime import date, timedelta


def previous_day(iso_date: str) -> str:
    return (date.fromisoformat(iso_date) - timedelta(days=1)).isoformat()
