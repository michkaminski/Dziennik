from __future__ import annotations

from app.adapters.inbound.web import create_app
from app.application.use_cases.sync_html import HtmlSync
from app.config import Settings, load_settings


def build_app(settings: Settings | None = None):
    cfg = settings or load_settings()
    return create_app(settings=cfg, syncer=HtmlSync(cfg))
