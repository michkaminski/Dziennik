from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_DATE = re.compile(r"(terminarz|wyniki)_(\d{4}-\d{2}-\d{2})", re.I)


@dataclass(frozen=True)
class ArchivedReport:
    kind: str
    path: Path
    file_name: str
    report_date: str | None


class ArchiveStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.terminarze = root / "terminarze"
        self.wyniki = root / "wyniki"
        self.versions = root / "versions"
        for path in (self.terminarze, self.wyniki, self.versions):
            path.mkdir(parents=True, exist_ok=True)

    def save(self, kind: str, file_name: str, content: bytes) -> tuple[Path, bool]:
        folder = self.terminarze if kind == "terminarz" else self.wyniki
        current = folder / file_name
        digest = hashlib.sha256(content).hexdigest()
        if current.exists() and hashlib.sha256(current.read_bytes()).hexdigest() == digest:
            return current, False
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        if current.exists():
            shutil.copy2(current, self.versions / f"{current.stem}__{stamp}{current.suffix}")
        current.write_bytes(content)
        return current, True

    def latest(self, kind: str) -> ArchivedReport | None:
        files = self._files(kind)
        if not files:
            return None
        return self._as_report(kind, files[0])

    def by_date(self, kind: str, report_date: str) -> ArchivedReport | None:
        for path in self._files(kind):
            if self._date(path.name) == report_date:
                return self._as_report(kind, path)
        return None

    def available_dates(self, kind: str | None = None) -> list[str]:
        kinds = (kind,) if kind else ("terminarz", "wyniki")
        dates = {
            date
            for item_kind in kinds
            for path in self._files(item_kind)
            if (date := self._date(path.name))
        }
        return sorted(dates, reverse=True)

    def _files(self, kind: str) -> list[Path]:
        folder = self.terminarze if kind == "terminarz" else self.wyniki
        files = [p for p in folder.glob("*.html") if p.is_file()]
        files.sort(key=self._sort_key, reverse=True)
        return files

    def _as_report(self, kind: str, path: Path) -> ArchivedReport:
        return ArchivedReport(
            kind=kind,
            path=path,
            file_name=path.name,
            report_date=self._date(path.name),
        )

    def _sort_key(self, path: Path) -> tuple:
        match = _DATE.search(path.name)
        date = match.group(2) if match else "0000-00-00"
        return date, path.stat().st_mtime

    def _date(self, name: str) -> str | None:
        match = _DATE.search(name)
        return match.group(2) if match else None
