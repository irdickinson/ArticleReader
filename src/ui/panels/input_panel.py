from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QFileDialog,
)


class InputPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(360)
        self._queued_sources: list[str] = []
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Public API used by MainWindow
    # ------------------------------------------------------------------

    def take_sources(self) -> list[str]:
        """Return queued sources and clear the queue."""
        sources = list(self._queued_sources)
        self._queued_sources.clear()
        self._refresh_queue_label()
        return sources

    def set_processing(self, active: bool) -> None:
        """Disable inputs while the worker is running."""
        self.url_input.setEnabled(not active)
        self.add_url_btn.setEnabled(not active)
        self.upload_btn.setEnabled(not active)
        self.process_btn.setEnabled(not active)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(10)

        # URL section
        url_label = QLabel("URL")
        url_label.setStyleSheet("font-weight: bold;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        self.add_url_btn = QPushButton("Add URL")
        self.add_url_btn.setEnabled(False)

        layout.addWidget(url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.add_url_btn)
        layout.addWidget(_divider())

        # File section
        file_label = QLabel("File")
        file_label.setStyleSheet("font-weight: bold;")
        self.upload_btn = QPushButton("Upload File (HTML / PDF)")

        layout.addWidget(file_label)
        layout.addWidget(self.upload_btn)
        layout.addWidget(_divider())

        # Queue status
        self.queue_label = QLabel("No sources queued")
        self.queue_label.setStyleSheet("color: grey; font-size: 11px;")
        self.queue_label.setWordWrap(True)
        layout.addWidget(self.queue_label)
        layout.addWidget(_divider())

        # Process
        self.process_btn = QPushButton("Process")
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self.url_input.textChanged.connect(self._on_url_text_changed)
        self.add_url_btn.clicked.connect(self._on_add_url)
        self.upload_btn.clicked.connect(self._on_upload_file)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_url_text_changed(self, text: str) -> None:
        self.add_url_btn.setEnabled(bool(text.strip()))

    def _on_add_url(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            return
        self._queued_sources.append(url)
        self.url_input.clear()
        self._refresh_queue_label()

    def _on_upload_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "Supported Files (*.html *.htm *.pdf);;HTML Files (*.html *.htm);;PDF Files (*.pdf)",
        )
        if path:
            self._queued_sources.append(path)
            self._refresh_queue_label()

    def _refresh_queue_label(self) -> None:
        count = len(self._queued_sources)
        if count == 0:
            self.queue_label.setText("No sources queued")
            self.process_btn.setEnabled(False)
        else:
            summary = _queue_summary(self._queued_sources)
            self.queue_label.setText(summary)
            self.process_btn.setEnabled(True)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _queue_summary(sources: list[str]) -> str:
    urls = sum(1 for s in sources if s.startswith("http"))
    pdfs = sum(1 for s in sources if not s.startswith("http") and Path(s).suffix.lower() == ".pdf")
    htmls = len(sources) - urls - pdfs

    parts: list[str] = []
    if urls:
        parts.append(f"{urls} URL{'s' if urls > 1 else ''}")
    if pdfs:
        parts.append(f"{pdfs} PDF{'s' if pdfs > 1 else ''}")
    if htmls:
        parts.append(f"{htmls} HTML file{'s' if htmls > 1 else ''}")
    return ", ".join(parts) + " queued"


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
