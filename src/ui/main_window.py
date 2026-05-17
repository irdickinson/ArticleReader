import ollama
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QStatusBar,
    QWidget,
)

from .panels.input_panel import InputPanel
from .panels.output_panel import OutputPanel
from core.worker import ProcessingWorker

_OLLAMA_CHECK_INTERVAL_MS = 10_000


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Article Reader")
        self.setMinimumSize(900, 600)
        self.resize(1200, 720)
        self._worker: ProcessingWorker | None = None
        self._build_ui()
        self._connect_signals()
        self._start_ollama_polling()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.input_panel = InputPanel()
        self.output_panel = OutputPanel()

        splitter.addWidget(self.input_panel)
        splitter.addWidget(self.output_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([280, 920])

        layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Throbber — shown only during processing
        self._throbber = QProgressBar()
        self._throbber.setRange(0, 0)
        self._throbber.setMaximumWidth(120)
        self._throbber.setMaximumHeight(16)
        self._throbber.hide()
        self.status_bar.addPermanentWidget(self._throbber)

        # Ollama status indicator
        self._ollama_label = QLabel()
        self._ollama_label.setContentsMargins(0, 0, 8, 0)
        self.status_bar.addPermanentWidget(self._ollama_label)

    def _connect_signals(self) -> None:
        self.input_panel.process_btn.clicked.connect(self._on_process)
        self.input_panel.open_note_requested.connect(self.output_panel.open_file)
        self.output_panel.tts_status.connect(self.status_bar.showMessage)

    def _start_ollama_polling(self) -> None:
        self._check_ollama_status()
        self._ollama_timer = QTimer(self)
        self._ollama_timer.setInterval(_OLLAMA_CHECK_INTERVAL_MS)
        self._ollama_timer.timeout.connect(self._check_ollama_status)
        self._ollama_timer.start()

    def _check_ollama_status(self) -> None:
        if _ollama_running():
            self._ollama_label.setText("● Ollama ready")
            self._ollama_label.setStyleSheet("color: #4caf50; font-size: 11px;")
        else:
            self._ollama_label.setText("● Ollama not running")
            self._ollama_label.setStyleSheet("color: #f44336; font-size: 11px;")

    def _on_process(self) -> None:
        sources = self.input_panel.take_sources()
        if not sources:
            return

        if not _ollama_running():
            QMessageBox.warning(
                self,
                "Ollama Not Running",
                "Ollama is not running.\n\n"
                "Please start Ollama and try again.\n\n"
                "If Ollama is installed, open it from the Start menu "
                "or run 'ollama serve' in a terminal.",
            )
            for s in sources:
                self.input_panel._queued_sources.append(s)
            self.input_panel._refresh_queue_label()
            return

        self.input_panel.set_processing(True)
        self.output_panel.clear()
        self._throbber.show()
        self.status_bar.showMessage("Starting…")

        self._worker = ProcessingWorker(
            sources, self.input_panel.detail_level, self.input_panel.sections
        )
        self._worker.progress.connect(self.status_bar.showMessage)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, markdown: str, notes_path: str) -> None:
        self._throbber.hide()
        if notes_path:
            self.output_panel.open_file(notes_path)
        else:
            self.output_panel.set_content(markdown)
        self.input_panel.set_processing(False)
        self.input_panel.refresh_history()
        self.input_panel.refresh_notes_tree()
        self.status_bar.showMessage("Done")

    def _on_error(self, message: str) -> None:
        self._throbber.hide()
        self.input_panel.set_processing(False)
        self.status_bar.showMessage(f"Error: {message}")


def _ollama_running() -> bool:
    try:
        ollama.list()
        return True
    except Exception:
        return False
