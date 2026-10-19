from __future__ import annotations

from dataclasses import dataclass

from app.adapters.outbound.archive_store import ArchiveStore
from app.adapters.outbound.drive_source import DriveHtmlSource
from app.config import Settings, load_settings


@dataclass(frozen=True)
class SyncResult:
    downloaded: int
    unchanged: int
    failed: int
    messages: tuple[str, ...]


class HtmlSync:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.source = DriveHtmlSource(self.settings)
        self.archive = ArchiveStore(self.settings.archive_dir)

    def run(self) -> SyncResult:
        downloaded = 0
        unchanged = 0
        failed = 0
        messages: list[str] = []
        try:
            files = self.source.list_html()
        except Exception as exc:
            return SyncResult(0, 0, 1, (f"Lista plików Drive: {exc}",))
        if not files:
            return SyncResult(0, 0, 0, ("Brak plików HTML terminarza/wyników na Drive.",))
        for item in files:
            try:
                content = self.source.download(item.file_id)
                if not content or b"<html" not in content[:2000].lower() and b"<!doctype" not in content[:2000].lower():
                    failed += 1
                    messages.append(f"Pominięto (nie wygląda na HTML): {item.name}")
                    continue
                _, changed = self.archive.save(item.kind, item.name, content)
                if changed:
                    downloaded += 1
                    messages.append(f"Zapisano: {item.name}")
                else:
                    unchanged += 1
                    messages.append(f"Bez zmian: {item.name}")
            except Exception as exc:
                failed += 1
                messages.append(f"Błąd {item.name}: {exc}")
        return SyncResult(downloaded, unchanged, failed, tuple(messages))
