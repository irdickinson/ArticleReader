from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QFileDialog,
)
from PyQt6.QtCore import Qt


class InputPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(360)
        self._queued_sources: list[str] = []
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(10)

        # --- URL section ---
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

        # --- HTML file section ---
        file_label = QLabel("HTML File")
        file_label.setStyleSheet("font-weight: bold;")

        self.upload_btn = QPushButton("Upload HTML File")

        layout.addWidget(file_label)
        layout.addWidget(self.upload_btn)

        layout.addWidget(_divider())

        # --- Queue status ---
        self.queue_label = QLabel("No sources queued")
        self.queue_label.setStyleSheet("color: grey; font-size: 11px;")
        self.queue_label.setWordWrap(True)
        layout.addWidget(self.queue_label)

        layout.addWidget(_divider())

        # --- Process button ---
        self.process_btn = QPushButton("Process")
        self.process_btn.setEnabled(False)

        layout.addWidget(self.process_btn)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self.url_input.textChanged.connect(self._on_url_text_changed)
        self.add_url_btn.clicked.connect(self._on_add_url)
        self.upload_btn.clicked.connect(self._on_upload_file)

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
            self, "Select HTML File", "", "HTML Files (*.html *.htm)"
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
            self.queue_label.setText(f"{count} source{'s' if count > 1 else ''} queued")
            self.process_btn.setEnabled(True)


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
