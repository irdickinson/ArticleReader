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

    def __init__(
        self,
        sources: list[str],
        detail_level: str = "standard",
        sections: dict[str, bool] | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__()
        self._sources = sources
        self._detail_level = detail_level
        self._sections = sections
        self._model = model
        self._raw_source_text: str = ""

    @property
    def raw_source_text(self) -> str:
        return self._raw_source_text

    def run(self) -> None:
        note_sections: list[str] = []
        source_sections: list[str] = []
        total = len(self._sources)
        history = HistoryStore()

        for i, source in enumerate(self._sources, start=1):
            label = source if source.startswith("http") else Path(source).name
            try:
                self.progress.emit(f"Extracting {i} of {total}: {label}")
                title, text = extract(source)
                source_sections.append(f"## Source {i}: {title}\n*{label}*\n\n{text}\n")
                self.progress.emit(f"Summarizing {i} of {total}: {title}")
                notes = summarize(text, self._detail_level, self._sections, self._model)
                note_sections.append(_format_section(i, title, source, notes))
                history.add(title, source, _source_type(source))
            except Exception as exc:
                note_sections.append(f"## Source {i}: {label}\n\n> Error: {exc}\n")

        today = date.today().strftime("%Y-%m-%d")
        markdown = f"# Notes — {today}\n\n" + "\n---\n\n".join(note_sections)
        self._raw_source_text = "\n---\n\n".join(source_sections)

        try:
            notes_path = save_processed_notes(markdown, self._sources)
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
