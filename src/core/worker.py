from datetime import date
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.extractor import extract
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

        for i, source in enumerate(self._sources, start=1):
            label = source if source.startswith("http") else Path(source).name
            try:
                self.progress.emit(f"Extracting {i} of {total}: {label}")
                title, text = extract(source)
                self.progress.emit(f"Summarizing {i} of {total}: {title}")
                notes = summarize(text)
                sections.append(_format_section(i, title, source, notes))
            except Exception as exc:
                sections.append(f"## Source {i}: {label}\n\n> Error: {exc}\n")

        today = date.today().strftime("%Y-%m-%d")
        output = f"# Notes — {today}\n\n" + "\n---\n\n".join(sections)
        self.finished.emit(output)


def _format_section(index: int, title: str, source: str, notes: str) -> str:
    label = source if source.startswith("http") else Path(source).name
    return f"## Source {index}: {title}\n*{label}*\n\n{notes}\n"
