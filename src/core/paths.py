from pathlib import Path

# src/core/paths.py → src/core → src → project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = PROJECT_ROOT / "uploads"
HISTORY_FILE = PROJECT_ROOT / "history.json"


def ensure_dirs() -> None:
    UPLOADS_DIR.mkdir(exist_ok=True)
