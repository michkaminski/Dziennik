from __future__ import annotations

from app.application.use_cases.sync_html import HtmlSync
from app.composition import build_app
from app.config import load_settings


def main() -> int:
    settings = load_settings()
    print("Synchronizacja HTML z Google Drive...")
    result = HtmlSync(settings).run()
    for line in result.messages:
        print(" ", line)
    print(
        f"Sync: zaktualizowano {result.downloaded}, "
        f"bez zmian {result.unchanged}, błędy {result.failed}"
    )
    app = build_app(settings)
    print(f"SPORTOMATYKA AI Dziennik -> http://{settings.flask_host}:{settings.flask_port}")
    app.run(host=settings.flask_host, port=settings.flask_port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
