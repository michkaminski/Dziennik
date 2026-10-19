from __future__ import annotations

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from app.adapters.outbound.archive_store import ArchiveStore
from app.application.use_cases.sync_html import HtmlSync
from app.config import Settings, load_settings
from app.domain.services.day_pair import previous_day


def create_app(
    settings: Settings | None = None,
    syncer: HtmlSync | None = None,
) -> Flask:
    cfg = settings or load_settings()
    root = cfg.root
    app = Flask(
        __name__,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
    )
    app.config["SECRET_KEY"] = cfg.secret_key
    store = ArchiveStore(cfg.archive_dir)
    sync_service = syncer or HtmlSync(cfg)

    @app.get("/")
    def index():
        dates = store.available_dates(kind="terminarz") or store.available_dates()
        selected = request.args.get("date") or (dates[0] if dates else None)
        if selected and selected not in dates:
            selected = dates[0] if dates else None
        wyniki_date = previous_day(selected) if selected else None
        terminarz = store.by_date("terminarz", selected) if selected else None
        wyniki = store.by_date("wyniki", wyniki_date) if wyniki_date else None
        return render_template(
            "index.html",
            dates=dates,
            selected_date=selected,
            wyniki_date=wyniki_date,
            terminarz=terminarz,
            wyniki=wyniki,
        )

    @app.get("/view/<kind>")
    def view(kind: str):
        if kind not in {"terminarz", "wyniki"}:
            abort(404)
        report_date = request.args.get("date")
        report = store.by_date(kind, report_date) if report_date else store.latest(kind)
        if report is None:
            abort(404)
        return report.path.read_text(encoding="utf-8", errors="replace")

    @app.post("/sync")
    def sync_now():
        result = sync_service.run()
        selected = request.form.get("date") or None
        if result.failed and not result.downloaded:
            flash(
                f"Sync z błędami: {result.failed}. " + " | ".join(result.messages[:3]),
                "danger",
            )
        else:
            flash(
                f"Sync: zaktualizowano {result.downloaded}, bez zmian {result.unchanged}, błędy {result.failed}",
                "ok",
            )
        return redirect(url_for("index", date=selected) if selected else url_for("index"))

    return app
