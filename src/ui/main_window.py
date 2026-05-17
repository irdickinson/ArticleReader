from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QStatusBar
from PyQt6.QtCore import Qt

from .panels.input_panel import InputPanel
from .panels.output_panel import OutputPanel
from core.worker import ProcessingWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Article Reader")
        self.setMinimumSize(900, 600)
        self.resize(1200, 720)
        self._worker: ProcessingWorker | None = None
        self._build_ui()
        self._connect_signals()

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

    def _connect_signals(self) -> None:
        self.input_panel.process_btn.clicked.connect(self._on_process)

    def _on_process(self) -> None:
        sources = self.input_panel.take_sources()
        if not sources:
            return

        self.input_panel.set_processing(True)
        self.output_panel.clear()
        self.status_bar.showMessage("Starting…")

        self._worker = ProcessingWorker(sources)
        self._worker.progress.connect(self.status_bar.showMessage)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, markdown: str) -> None:
        self.output_panel.set_content(markdown)
        self.input_panel.set_processing(False)
        self.status_bar.showMessage("Done")

    def _on_error(self, message: str) -> None:
        self.input_panel.set_processing(False)
        self.status_bar.showMessage(f"Error: {message}")
