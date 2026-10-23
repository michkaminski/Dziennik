# SPORTOMATYKA AI Dziennik (HTML)

Pobiera z Google Drive HTML terminarza i wyników, archiwizuje i pokazuje na jednej stronie.

## Uruchomienie

```bash
run_ai_dziennik.bat
# albo (Git Bash / Linux):
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

### Linux — usługa systemd

W katalogu projektu, raz:

```bash
bash scripts/install-systemd.sh
```

To usługa użytkownika `ai-dziennik`: start przy bootcie (linger, bez zalogowania) i restart po awarii. Procesem jest `run_ai_dziennik.sh` (venv, zależności, `run.py`). Nasłuch z `.env`: `FLASK_HOST` / `FLASK_PORT`.

```bash
systemctl --user status ai-dziennik
journalctl --user -u ai-dziennik -f
systemctl --user restart ai-dziennik
```

W Cockpit (start, stop, restart) widać usługę systemową. Ta komenda wyłącza usługę użytkownika i zakłada systemową; proces zostaje na koncie, które ją uruchamia (`User=`, u Ciebie `michal`):

```bash
bash scripts/install-systemd.sh system
```

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
