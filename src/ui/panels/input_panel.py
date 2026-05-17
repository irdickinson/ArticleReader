from datetime import datetime
from pathlib import Path

from core.extractor import is_youtube_url
from core.history import HistoryStore
from core.notes_store import create_folder, create_note, is_safe
from core.paths import NOTES_DIR
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

_TYPE_LABELS = {"youtube": "YT", "url": "URL", "pdf": "PDF", "html": "HTML"}


class InputPanel(QWidget):
    open_note_requested = pyqtSignal(str)   # absolute path to a .md file

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(380)
        self._queued_sources: list[str] = []
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Public API
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
        for entry in HistoryStore().entries():
            self._history_list.addItem(_make_history_item(entry))

    def refresh_notes_tree(self) -> None:
        self._notes_tree.clear()
        if NOTES_DIR.exists():
            _populate_tree(self._notes_tree.invisibleRootItem(), NOTES_DIR, self)

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
        self._tabs.addTab(self._build_notes_tab(), "Notes")
        layout.addWidget(self._tabs)

    def _build_add_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(10)

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

        file_label = QLabel("File")
        file_label.setStyleSheet("font-weight: bold;")
        self.upload_btn = QPushButton("Upload File (HTML / PDF)")

        layout.addWidget(file_label)
        layout.addWidget(self.upload_btn)
        layout.addWidget(_divider())

        self.queue_label = QLabel("No sources queued")
        self.queue_label.setStyleSheet("color: grey; font-size: 11px;")
        self.queue_label.setWordWrap(True)
        layout.addWidget(self.queue_label)
        layout.addWidget(_divider())

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

        btn_row = QHBoxLayout()
        self._open_notes_btn = QPushButton("Open Notes")
        self._open_notes_btn.setEnabled(False)
        self._requeue_btn = QPushButton("Re-queue")
        self._requeue_btn.setEnabled(False)
        btn_row.addWidget(self._open_notes_btn)
        btn_row.addWidget(self._requeue_btn)
        layout.addLayout(btn_row)

        self.refresh_history()
        return widget

    def _build_notes_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(8)

        btn_row = QHBoxLayout()
        self._new_note_btn = QPushButton("New Note")
        self._new_folder_btn = QPushButton("New Folder")
        btn_row.addWidget(self._new_note_btn)
        btn_row.addWidget(self._new_folder_btn)
        layout.addLayout(btn_row)

        self._notes_tree = QTreeWidget()
        self._notes_tree.setHeaderHidden(True)
        self._notes_tree.setAnimated(True)
        layout.addWidget(self._notes_tree)

        self.refresh_notes_tree()
        return widget

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self.url_input.textChanged.connect(self._on_url_changed)
        self.add_url_btn.clicked.connect(self._on_add_url)
        self.upload_btn.clicked.connect(self._on_upload_file)
        self._history_list.itemSelectionChanged.connect(self._on_history_selection)
        self._history_list.itemDoubleClicked.connect(self._on_history_double_click)
        self._open_notes_btn.clicked.connect(self._on_open_notes)
        self._requeue_btn.clicked.connect(self._on_requeue)
        self._notes_tree.itemDoubleClicked.connect(self._on_notes_item_double_click)
        self._new_note_btn.clicked.connect(self._on_new_note)
        self._new_folder_btn.clicked.connect(self._on_new_folder)

    def _on_url_changed(self, text: str) -> None:
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
            self, "Select File", "",
            "Supported Files (*.html *.htm *.pdf);;HTML Files (*.html *.htm);;PDF Files (*.pdf)",
        )
        if path:
            self._queued_sources.append(path)
            self._refresh_queue_label()

    def _on_history_selection(self) -> None:
        item = self._history_list.currentItem()
        if not item:
            self._open_notes_btn.setEnabled(False)
            self._requeue_btn.setEnabled(False)
            return
        notes_path = item.data(Qt.ItemDataRole.UserRole + 1)
        self._open_notes_btn.setEnabled(bool(notes_path and Path(notes_path).exists()))
        self._requeue_btn.setEnabled(True)

    def _on_history_double_click(self, item: QListWidgetItem) -> None:
        notes_path = item.data(Qt.ItemDataRole.UserRole + 1)
        if notes_path and Path(notes_path).exists():
            self.open_note_requested.emit(notes_path)

    def _on_open_notes(self) -> None:
        item = self._history_list.currentItem()
        if not item:
            return
        notes_path = item.data(Qt.ItemDataRole.UserRole + 1)
        if notes_path and Path(notes_path).exists():
            self.open_note_requested.emit(notes_path)

    def _on_requeue(self) -> None:
        item = self._history_list.currentItem()
        if not item:
            return
        source = item.data(Qt.ItemDataRole.UserRole)
        if source:
            self._queued_sources.append(source)
            self._refresh_queue_label()
            self._tabs.setCurrentIndex(0)

    def _on_notes_item_double_click(self, item: QTreeWidgetItem, _col: int) -> None:
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and Path(path).is_file():
            self.open_note_requested.emit(path)

    def _on_new_note(self) -> None:
        folder = self._selected_notes_folder()
        name, ok = QInputDialog.getText(self, "New Note", "Note name:")
        if not ok or not name.strip():
            return
        try:
            path = create_note(name.strip(), folder)
            self.refresh_notes_tree()
            self.open_note_requested.emit(str(path))
            self._tabs.setCurrentIndex(2)
        except ValueError as exc:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Path", str(exc))

    def _on_new_folder(self) -> None:
        parent = self._selected_notes_folder()
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not name.strip():
            return
        try:
            create_folder(name.strip(), parent)
            self.refresh_notes_tree()
        except ValueError as exc:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Path", str(exc))

    def _selected_notes_folder(self) -> Path | None:
        item = self._notes_tree.currentItem()
        if not item:
            return None
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if not path_str:
            return None
        path = Path(path_str)
        candidate = path if path.is_dir() else path.parent
        return candidate if is_safe(candidate) else None

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

def _populate_tree(parent_item: QTreeWidgetItem, folder: Path, panel: InputPanel) -> None:
    dirs = sorted(p for p in folder.iterdir() if p.is_dir())
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.name != ".gitkeep")

    style = panel.style()
    dir_icon = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
    file_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    for d in dirs:
        item = QTreeWidgetItem([d.name])
        item.setIcon(0, dir_icon)
        item.setData(0, Qt.ItemDataRole.UserRole, str(d))
        _populate_tree(item, d, panel)
        parent_item.addChild(item)

    for f in files:
        item = QTreeWidgetItem([f.name])
        item.setIcon(0, file_icon)
        item.setData(0, Qt.ItemDataRole.UserRole, str(f))
        parent_item.addChild(item)


def _make_history_item(entry) -> QListWidgetItem:
    type_label = _TYPE_LABELS.get(entry.source_type, "?")
    try:
        dt = datetime.fromisoformat(entry.processed_at)
        date_str = dt.strftime("%b %d, %Y")
    except ValueError:
        date_str = entry.processed_at[:10]

    has_notes = bool(entry.notes_path and Path(entry.notes_path).exists())
    suffix = " 📄" if has_notes else ""
    item = QListWidgetItem(f"[{type_label}] {entry.title}{suffix}\n{date_str}")
    item.setData(Qt.ItemDataRole.UserRole, entry.requeue_path)
    item.setData(Qt.ItemDataRole.UserRole + 1, entry.notes_path)
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
