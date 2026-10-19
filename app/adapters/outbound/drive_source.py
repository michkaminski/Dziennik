from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.request import Request, urlopen

from app.config import Settings

_UA = "Mozilla/5.0 SportomatykaDziennik/1.0"
_NAME_RE = re.compile(
    r'data-id="([a-zA-Z0-9_-]{20,})"[^>]{0,500}?data-tooltip="((?:terminarz|wyniki)_[^"]+\.html)"',
    re.I,
)
_NAME_RE_ALT = re.compile(
    r'data-tooltip="((?:terminarz|wyniki)_[^"]+\.html)"[^>]{0,500}?data-id="([a-zA-Z0-9_-]{20,})"',
    re.I,
)


@dataclass(frozen=True)
class DriveHtmlFile:
    file_id: str
    name: str
    kind: str


class DriveHtmlSource:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def list_html(self) -> list[DriveHtmlFile]:
        files: list[DriveHtmlFile] = []
        files.extend(self._list_folder(self._settings.drive_folder_terminarze, "terminarz"))
        files.extend(self._list_folder(self._settings.drive_folder_wyniki, "wyniki"))
        return self._prefer_main_reports(files)

    def download(self, file_id: str) -> bytes:
        if self._oauth_ready():
            try:
                return self._download_oauth(file_id)
            except Exception:
                pass
        return self._download_public(file_id)

    def _list_folder(self, folder_id: str, kind: str) -> list[DriveHtmlFile]:
        if self._oauth_ready():
            try:
                return self._list_oauth(folder_id, kind)
            except Exception:
                pass
        return self._list_public(folder_id, kind)

    def _prefer_main_reports(self, files: list[DriveHtmlFile]) -> list[DriveHtmlFile]:
        chosen: dict[tuple[str, str], DriveHtmlFile] = {}
        for item in files:
            if "_z_json" in item.name.lower() or item.name.startswith("."):
                continue
            if not item.name.lower().endswith(".html"):
                continue
            match = re.search(r"(terminarz|wyniki)_(\d{4}-\d{2}-\d{2})", item.name, re.I)
            if not match:
                continue
            key = (match.group(1).lower(), match.group(2))
            prev = chosen.get(key)
            if prev is None or len(item.name) < len(prev.name):
                chosen[key] = DriveHtmlFile(item.file_id, item.name, match.group(1).lower())
        return list(chosen.values())

    def _oauth_ready(self) -> bool:
        return bool(
            self._settings.google_client_id
            and self._settings.google_client_secret
            and self._settings.google_token_path.exists()
        )

    def _list_public(self, folder_id: str, kind: str) -> list[DriveHtmlFile]:
        html = self._http(f"https://drive.google.com/drive/folders/{folder_id}")
        found: dict[str, DriveHtmlFile] = {}
        for match in _NAME_RE.finditer(html):
            file_id, name = match.group(1), match.group(2)
            if kind in name.lower():
                found[file_id] = DriveHtmlFile(file_id, name, kind)
        for match in _NAME_RE_ALT.finditer(html):
            name, file_id = match.group(1), match.group(2)
            if kind in name.lower():
                found[file_id] = DriveHtmlFile(file_id, name, kind)
        if not found:
            for name_match in re.finditer(
                rf"((?:{kind})_[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}(?:_[^\"\\]+)?\.html)",
                html,
                re.I,
            ):
                name = name_match.group(1)
                window = html[max(0, name_match.start() - 500) : name_match.end() + 200]
                id_match = re.search(r'data-id="([a-zA-Z0-9_-]{20,})"', window)
                if id_match:
                    found[id_match.group(1)] = DriveHtmlFile(id_match.group(1), name, kind)
        return list(found.values())

    def _download_public(self, file_id: str) -> bytes:
        data = self._http_bytes(
            f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
        )
        if data.lstrip().startswith(b"<!DOCTYPE") or data.lstrip().startswith(b"<html"):
            data = self._http_bytes(
                f"https://drive.google.com/uc?id={file_id}&export=download&confirm=t"
            )
        return data

    def _list_oauth(self, folder_id: str, kind: str) -> list[DriveHtmlFile]:
        service = self._drive_service()
        query = (
            f"'{folder_id}' in parents and trashed = false "
            f"and mimeType != 'application/vnd.google-apps.folder'"
        )
        response = (
            service.files()
            .list(q=query, fields="files(id,name)", pageSize=200)
            .execute()
        )
        out: list[DriveHtmlFile] = []
        for item in response.get("files", []):
            name = item.get("name") or ""
            if kind in name.lower() and name.lower().endswith(".html"):
                out.append(DriveHtmlFile(item["id"], name, kind))
        return out

    def _download_oauth(self, file_id: str) -> bytes:
        import io

        from googleapiclient.http import MediaIoBaseDownload

        service = self._drive_service()
        request = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buffer.getvalue()

    def _drive_service(self):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        token_path = self._settings.google_token_path
        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": self._settings.google_client_id,
                            "client_secret": self._settings.google_client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost"],
                        }
                    },
                    scopes,
                )
                creds = flow.run_local_server(port=0)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json(), encoding="utf-8")
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    def _http(self, url: str) -> str:
        return self._http_bytes(url).decode("utf-8", errors="replace")

    def _http_bytes(self, url: str) -> bytes:
        request = Request(url, headers={"User-Agent": _UA})
        with urlopen(request, timeout=60) as response:
            return response.read()


def run_drive_auth(settings: Settings) -> None:
    source = DriveHtmlSource(settings)
    source._drive_service()
    print(f"Token zapisany: {settings.google_token_path}")
