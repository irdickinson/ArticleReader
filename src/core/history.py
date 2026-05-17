import json
import shutil
from datetime import datetime
from pathlib import Path

from core.paths import HISTORY_FILE, UPLOADS_DIR, ensure_dirs


class HistoryEntry:
    def __init__(
        self,
        title: str,
        source: str,
        source_type: str,
        processed_at: str,
        cached_path: str | None = None,
    ) -> None:
        self.title = title
        self.source = source
        self.source_type = source_type
        self.processed_at = processed_at
        self.cached_path = cached_path

    @property
    def requeue_path(self) -> str:
        """The path/URL to re-add to the queue."""
        return self.cached_path if self.cached_path else self.source

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "source_type": self.source_type,
            "processed_at": self.processed_at,
            "cached_path": self.cached_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            title=data["title"],
            source=data["source"],
            source_type=data["source_type"],
            processed_at=data["processed_at"],
            cached_path=data.get("cached_path"),
        )


class HistoryStore:
    def __init__(self) -> None:
        ensure_dirs()
        self._entries: list[HistoryEntry] = self._load()

    def add(self, title: str, source: str, source_type: str) -> HistoryEntry:
        cached_path = None
        if source_type in ("pdf", "html") and not source.startswith("http"):
            cached_path = _cache_file(source)

        entry = HistoryEntry(
            title=title,
            source=source,
            source_type=source_type,
            processed_at=datetime.now().isoformat(timespec="seconds"),
            cached_path=cached_path,
        )
        self._entries.insert(0, entry)
        self._save()
        return entry

    def entries(self) -> list[HistoryEntry]:
        return list(self._entries)

    def _load(self) -> list[HistoryEntry]:
        if not HISTORY_FILE.exists():
            return []
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            return [HistoryEntry.from_dict(e) for e in data]
        except Exception:
            return []

    def _save(self) -> None:
        HISTORY_FILE.write_text(
            json.dumps([e.to_dict() for e in self._entries], indent=2),
            encoding="utf-8",
        )


def _cache_file(source_path: str) -> str | None:
    """Copy a local file into uploads/ with a timestamp prefix."""
    src = Path(source_path)
    if not src.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = UPLOADS_DIR / f"{timestamp}_{src.name}"
    shutil.copy2(src, dest)
    return str(dest)
