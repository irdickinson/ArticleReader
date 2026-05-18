import sys
from pathlib import Path

# When running as a PyInstaller bundle, sys.frozen is True and sys.executable
# points to the exe. Data files live next to the exe.
# In development, data files live at the project root (parent of src/).
if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

UPLOADS_DIR = PROJECT_ROOT / "uploads"
NOTES_DIR = PROJECT_ROOT / "notes"
HISTORY_FILE = PROJECT_ROOT / "history.json"


def ensure_dirs() -> None:
    UPLOADS_DIR.mkdir(exist_ok=True)
    NOTES_DIR.mkdir(exist_ok=True)
