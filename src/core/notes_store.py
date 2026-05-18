import re
from datetime import datetime
from pathlib import Path

from core.paths import NOTES_DIR, ensure_dirs


def save_processed_notes(content: str, sources: list[str]) -> Path:
    """Auto-save notes produced by the processing worker."""
    ensure_dirs()
    stem = _auto_stem(sources)
    path = _unique_path(NOTES_DIR / f"{stem}.md")
    path.write_text(content, encoding="utf-8")
    return path


def create_note(name: str, folder: Path | None = None) -> Path:
    """Create a new empty note inside notes/ (or a subfolder of it)."""
    ensure_dirs()
    base = folder if folder else NOTES_DIR
    _assert_safe(base)
    if not name.endswith(".md"):
        name += ".md"
    path = _unique_path(base / _sanitize(name))
    path.write_text("", encoding="utf-8")
    return path


def create_folder(name: str, parent: Path | None = None) -> Path:
    """Create a new subfolder inside notes/."""
    ensure_dirs()
    base = parent if parent else NOTES_DIR
    _assert_safe(base)
    path = base / _sanitize(name)
    _assert_safe(path)
    path.mkdir(exist_ok=True)
    return path


def is_safe(path: Path) -> bool:
    """Return True if path is inside NOTES_DIR."""
    try:
        path.resolve().relative_to(NOTES_DIR.resolve())
        return True
    except ValueError:
        return False


# ------------------------------------------------------------------
# Internals
# ------------------------------------------------------------------

def _assert_safe(path: Path) -> None:
    if not is_safe(path):
        raise ValueError(f"Path '{path}' is outside the notes directory.")


def _auto_stem(sources: list[str]) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    if len(sources) == 1:
        from pathlib import Path as _P
        label = sources[0]
        if label.startswith("http"):
            # Use last path segment of URL or domain
            from urllib.parse import urlparse
            parsed = urlparse(label)
            segment = parsed.path.rstrip("/").split("/")[-1] or parsed.netloc
            label = segment
        else:
            label = _P(label).stem
        return f"{_slugify(label)}-{timestamp}"
    return f"notes-{timestamp}"


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text[:48] or "note"


def _sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "-", name).strip()


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        candidate = path.parent / f"{stem}-{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1
