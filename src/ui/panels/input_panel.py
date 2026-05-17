from datetime import datetime
from pathlib import Path

from core.extractor import is_youtube_url
from core.history import HistoryStore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QFileDialog,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
)

_TYPE_LABELS = {
    "youtube": "YT",
    "url": "URL",
    "pdf": "PDF",
    "html": "HTML",
}


class InputPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(380)
        self._queued_sources: list[str] = []
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Public API used by MainWindow
    # ------------------------------------------------------------------

    def take_sources(self) -> list[str]:
        sources = list(self._queued_sources)
        self._queued_sources.clear()
        self._refresh_queue_label()
        return sources

    def set_processing(self, active: bool) -> None:
        self.url_input.setEnabled(not active)
        self.add_url_btn.setEnabled(not active)
        self.upload_btn.setEnabled(not active)
        self.process_btn.setEnabled(not active)

    def refresh_history(self) -> None:
        self._history_list.clear()
        store = HistoryStore()
        for entry in store.entries():
            self._history_list.addItem(_make_history_item(entry))

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_add_tab(), "Add Sources")
        self._tabs.addTab(self._build_history_tab(), "History")
        layout.addWidget(self._tabs)

    def _build_add_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(10)

        # URL
        url_label = QLabel("URL")
        url_label.setStyleSheet("font-weight: bold;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://... or YouTube link")
        self.add_url_btn = QPushButton("Add URL")
        self.add_url_btn.setEnabled(False)

        layout.addWidget(url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.add_url_btn)
        layout.addWidget(_divider())

        # File
        file_label = QLabel("File")
        file_label.setStyleSheet("font-weight: bold;")
        self.upload_btn = QPushButton("Upload File (HTML / PDF)")

        layout.addWidget(file_label)
        layout.addWidget(self.upload_btn)
        layout.addWidget(_divider())

        # Queue
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

        return widget

    def _build_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(8)

        self._history_list = QListWidget()
        self._history_list.setWordWrap(True)
        self._history_list.setSpacing(2)
        layout.addWidget(self._history_list)

        self._requeue_btn = QPushButton("Add to Queue")
        self._requeue_btn.setEnabled(False)
        layout.addWidget(self._requeue_btn)

        self.refresh_history()
        return widget

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self.url_input.textChanged.connect(self._on_url_text_changed)
        self.add_url_btn.clicked.connect(self._on_add_url)
        self.upload_btn.clicked.connect(self._on_upload_file)
        self._history_list.itemSelectionChanged.connect(self._on_history_selection)
        self._requeue_btn.clicked.connect(self._on_requeue)

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

    def _on_history_selection(self) -> None:
        self._requeue_btn.setEnabled(bool(self._history_list.selectedItems()))

    def _on_requeue(self) -> None:
        item = self._history_list.currentItem()
        if not item:
            return
        source = item.data(Qt.ItemDataRole.UserRole)
        if source:
            self._queued_sources.append(source)
            self._refresh_queue_label()
            self._tabs.setCurrentIndex(0)

    def _refresh_queue_label(self) -> None:
        count = len(self._queued_sources)
        if count == 0:
            self.queue_label.setText("No sources queued")
            self.process_btn.setEnabled(False)
        else:
            self.queue_label.setText(_queue_summary(self._queued_sources))
            self.process_btn.setEnabled(True)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_history_item(entry) -> QListWidgetItem:
    type_label = _TYPE_LABELS.get(entry.source_type, "?")
    try:
        dt = datetime.fromisoformat(entry.processed_at)
        date_str = dt.strftime("%b %d, %Y")
    except ValueError:
        date_str = entry.processed_at[:10]

    item = QListWidgetItem(f"[{type_label}] {entry.title}\n{date_str}")
    item.setData(Qt.ItemDataRole.UserRole, entry.requeue_path)
    item.setToolTip(entry.source)
    return item


def _queue_summary(sources: list[str]) -> str:
    youtube = sum(1 for s in sources if s.startswith("http") and is_youtube_url(s))
    urls = sum(1 for s in sources if s.startswith("http") and not is_youtube_url(s))
    pdfs = sum(1 for s in sources if not s.startswith("http") and Path(s).suffix.lower() == ".pdf")
    htmls = len(sources) - youtube - urls - pdfs

    parts: list[str] = []
    if youtube:
        parts.append(f"{youtube} YouTube video{'s' if youtube > 1 else ''}")
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
