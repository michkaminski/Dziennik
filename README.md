# SPORTOMATYKA AI Dziennik (HTML)

Pobiera z Google Drive HTML terminarza i wyników, archiwizuje i pokazuje na jednej stronie.

## Uruchomienie

```bash
run_ai_dziennik.bat
# albo (Git Bash / Linux, wspólny venv w ../.venv):
./run_ai_dziennik.sh
```

albo:

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
python run.py
```

Adres: http://127.0.0.1:2613

- przy starcie: sync z Drive
- przycisk **Pobierz z Dysku** na stronie
- ręcznie: `python -m app.sync_cli`

## Struktura

```text
run.py                 ← start
app/
  domain/              ← daty (terminarz vs wyniki -1 dzień)
  application/         ← sync HTML
  adapters/
    inbound/           ← Flask (surowy HTML z archiwum)
    outbound/          ← Drive, archiwum
templates/ static/ data/
```

## Archiwum

```text
data/archive/terminarze/
data/archive/wyniki/
data/archive/versions/
```

## Drive

Foldery (`.env`): `DRIVE_FOLDER_TERMINARZE`, `DRIVE_FOLDER_WYNIKI`.  
Domyślnie pobieranie publiczne. OAuth:

```bash
python -c "from app.config import load_settings; from app.adapters.outbound.drive_source import run_drive_auth; run_drive_auth(load_settings())"
```
