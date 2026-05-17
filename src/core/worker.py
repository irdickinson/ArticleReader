from datetime import date
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.extractor import extract, is_youtube_url
from core.history import HistoryStore
from core.notes_store import save_processed_notes
from core.summarizer import summarize


class ProcessingWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)  # (markdown, saved_notes_path)
    error = pyqtSignal(str)

    def __init__(self, sources: list[str]) -> None:
        super().__init__()
        self._sources = sources

    def run(self) -> None:
        sections: list[str] = []
        total = len(self._sources)
        history = HistoryStore()

        for i, source in enumerate(self._sources, start=1):
            label = source if source.startswith("http") else Path(source).name
            try:
                self.progress.emit(f"Extracting {i} of {total}: {label}")
                title, text = extract(source)
                self.progress.emit(f"Summarizing {i} of {total}: {title}")
                notes = summarize(text)
                sections.append(_format_section(i, title, source, notes))
                history.add(title, source, _source_type(source))
            except Exception as exc:
                sections.append(f"## Source {i}: {label}\n\n> Error: {exc}\n")

        today = date.today().strftime("%Y-%m-%d")
        markdown = f"# Notes — {today}\n\n" + "\n---\n\n".join(sections)

        try:
            notes_path = save_processed_notes(markdown, self._sources)
            # Back-fill notes_path on the entries we just added
            store = HistoryStore()
            for entry in store.entries()[:total]:
                entry.notes_path = str(notes_path)
            store._save()
        except Exception:
            notes_path = None

        self.finished.emit(markdown, str(notes_path) if notes_path else "")


def _source_type(source: str) -> str:
    if source.startswith("http"):
        return "youtube" if is_youtube_url(source) else "url"
    return "pdf" if Path(source).suffix.lower() == ".pdf" else "html"


def _format_section(index: int, title: str, source: str, notes: str) -> str:
    label = source if source.startswith("http") else Path(source).name
    return f"## Source {index}: {title}\n*{label}*\n\n{notes}\n"
