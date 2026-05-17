from datetime import date
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.extractor import extract, is_youtube_url
from core.history import HistoryStore
from core.summarizer import summarize


class ProcessingWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
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
        output = f"# Notes — {today}\n\n" + "\n---\n\n".join(sections)
        self.finished.emit(output)


def _source_type(source: str) -> str:
    if source.startswith("http"):
        return "youtube" if is_youtube_url(source) else "url"
    suffix = Path(source).suffix.lower()
    return "pdf" if suffix == ".pdf" else "html"


def _format_section(index: int, title: str, source: str, notes: str) -> str:
    label = source if source.startswith("http") else Path(source).name
    return f"## Source {index}: {title}\n*{label}*\n\n{notes}\n"
