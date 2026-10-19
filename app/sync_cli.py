from __future__ import annotations

from app.application.use_cases.sync_html import HtmlSync


def main() -> int:
    result = HtmlSync().run()
    for line in result.messages:
        print(line)
    print(
        f"Gotowe: pobrano/zaktualizowano {result.downloaded}, "
        f"bez zmian {result.unchanged}, błędy {result.failed}"
    )
    return 1 if result.failed and not result.downloaded else 0


if __name__ == "__main__":
    raise SystemExit(main())
