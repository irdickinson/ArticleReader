from datetime import date
from pathlib import Path

import markdown as md
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QPalette, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.tts_worker import SPEEDS, VOLUMES, VOICES, TTSWorker


def _build_css() -> str:
    palette = QApplication.instance().palette()
    bg = palette.color(QPalette.ColorRole.Base)
    dark_mode = bg.lightness() < 128

    if dark_mode:
        text      = "#e8e8e8"
        muted     = "#b0b0b0"
        h1_border = "#555"
        hr_color  = "#444"
        bq_border = "#666"
        code_bg   = "#2c2c2c"
    else:
        text      = "#1a1a1a"
        muted     = "#555"
        h1_border = "#ddd"
        hr_color  = "#e0e0e0"
        bq_border = "#aaa"
        code_bg   = "#f4f4f4"

    return f"""<style>
body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    line-height: 1.7;
    color: {text};
    padding: 4px 8px;
}}
h1 {{ font-size: 18px; border-bottom: 1px solid {h1_border}; padding-bottom: 6px; margin-bottom: 12px; }}
h2 {{ font-size: 15px; margin-top: 24px; margin-bottom: 6px; }}
h3 {{ font-size: 13px; margin-top: 16px; margin-bottom: 4px; }}
blockquote {{
    border-left: 3px solid {bq_border};
    margin: 6px 0 6px 12px;
    padding: 2px 10px;
    color: {muted};
    font-style: italic;
}}
ul {{ padding-left: 20px; }}
li {{ margin-bottom: 4px; }}
hr {{ border: none; border-top: 1px solid {hr_color}; margin: 20px 0; }}
strong {{ font-weight: 600; }}
code {{ background: {code_bg}; padding: 1px 4px; border-radius: 3px; font-family: Consolas, monospace; }}
pre {{ background: {code_bg}; padding: 10px; border-radius: 4px; white-space: pre-wrap; word-break: break-word; }}
</style>"""


class OutputPanel(QWidget):
    tts_status = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._raw_content = ""
        self._raw_source = ""
        self._current_file: Path | None = None
        self._dirty = False
        self._viewing_source = False
        self._last_save_dir = ""
        self._tts_worker: TTSWorker | None = None
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_file(self, path: str) -> None:
        self._stop_tts()
        p = Path(path)
        try:
            content = p.read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Open Failed", str(exc))
            return
        self._current_file = p
        self._dirty = False
        self._raw_content = content
        self._load_into_editor(content)
        self._exit_source_view()
        self._render()
        self._update_file_label()
        has_content = bool(content.strip())
        self._edit_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self._copy_btn.setEnabled(has_content)
        self._read_btn.setEnabled(has_content)
        if not has_content:
            self._edit_btn.setChecked(True)

    def set_content(self, markdown: str, file_path: str = "") -> None:
        self._stop_tts()
        self._current_file = Path(file_path) if file_path else None
        self._dirty = False
        self._raw_content = markdown
        self._load_into_editor(markdown)
        self._exit_source_view()
        self._render()
        self._update_file_label()
        has_content = bool(markdown.strip())
        self._set_buttons_enabled(has_content)

    def set_raw_source(self, text: str) -> None:
        self._raw_source = text
        has_source = bool(text.strip())
        self._source_btn.setEnabled(has_source)
        if not has_source and self._viewing_source:
            self._source_btn.setChecked(False)

    def clear(self) -> None:
        self._stop_tts()
        self._raw_content = ""
        self._raw_source = ""
        self._current_file = None
        self._dirty = False
        self._exit_source_view()
        self._browser.clear()
        self._load_into_editor("")
        self._set_buttons_enabled(False)
        self._source_btn.setEnabled(False)
        self._file_label.setText("Notes")

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        # Row 1: file label + note controls
        header_row = QHBoxLayout()
        self._file_label = QLabel("Notes")
        self._file_label.setStyleSheet("font-weight: bold; font-size: 15px;")

        self._source_btn = QToolButton()
        self._source_btn.setText("Source Text")
        self._source_btn.setCheckable(True)
        self._source_btn.setEnabled(False)
        self._source_btn.setToolTip("View the original extracted text / transcript")

        self._edit_btn = QToolButton()
        self._edit_btn.setText("Edit")
        self._edit_btn.setCheckable(True)
        self._edit_btn.setEnabled(False)
        self._edit_btn.setToolTip("Toggle edit mode (Ctrl+S to save)")

        self._copy_btn = QToolButton()
        self._copy_btn.setText("Copy")
        self._copy_btn.setEnabled(False)
        self._copy_btn.setToolTip("Copy to clipboard")

        self.save_btn = QPushButton("Save")
        self.save_btn.setEnabled(False)

        header_row.addWidget(self._file_label)
        header_row.addStretch()
        header_row.addWidget(self._source_btn)
        header_row.addWidget(self._edit_btn)
        header_row.addWidget(self._copy_btn)
        header_row.addWidget(self.save_btn)
        layout.addLayout(header_row)

        # Row 2: TTS controls
        tts_row = QHBoxLayout()
        self._read_btn = QToolButton()
        self._read_btn.setText("▶  Read Aloud")
        self._read_btn.setEnabled(False)

        self._stop_btn = QToolButton()
        self._stop_btn.setText("■  Stop")
        self._stop_btn.setEnabled(False)

        self._volume_combo = QComboBox()
        for label in VOLUMES:
            self._volume_combo.addItem(label)
        self._volume_combo.setCurrentText("100%")
        self._volume_combo.setToolTip("Volume")
        self._volume_combo.setMaximumWidth(64)

        self._speed_combo = QComboBox()
        for label in SPEEDS:
            self._speed_combo.addItem(label)
        self._speed_combo.setCurrentText("1×")
        self._speed_combo.setToolTip("Speed")
        self._speed_combo.setMaximumWidth(64)

        self._voice_combo = QComboBox()
        for display_name in VOICES:
            self._voice_combo.addItem(display_name)
        self._voice_combo.setToolTip("Voice")

        tts_row.addWidget(self._read_btn)
        tts_row.addWidget(self._stop_btn)
        tts_row.addStretch()
        tts_row.addWidget(QLabel("Vol:"))
        tts_row.addWidget(self._volume_combo)
        tts_row.addWidget(QLabel("Speed:"))
        tts_row.addWidget(self._speed_combo)
        tts_row.addWidget(QLabel("Voice:"))
        tts_row.addWidget(self._voice_combo)
        layout.addLayout(tts_row)

        # Content area
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setPlaceholderText(
            "Processed notes will appear here.\n\n"
            "Add URLs or files on the left, then press Process."
        )
        layout.addWidget(self._browser)

        self._editor = QTextEdit()
        self._editor.setFont(QFont("Consolas", 11))
        self._editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._editor.hide()
        layout.addWidget(self._editor)

    def _connect_signals(self) -> None:
        self.save_btn.clicked.connect(self._on_save)
        self._copy_btn.clicked.connect(self._on_copy)
        self._edit_btn.toggled.connect(self._on_toggle_edit)
        self._source_btn.toggled.connect(self._on_toggle_source)
        self._editor.textChanged.connect(self._on_text_changed)
        self._read_btn.clicked.connect(self._on_read_aloud)
        self._stop_btn.clicked.connect(self._on_stop_tts)

        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self._on_save)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_copy(self) -> None:
        text = self._raw_source if self._viewing_source else self._raw_content
        QApplication.clipboard().setText(text)
        self._copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self._copy_btn.setText("Copy"))

    def _on_toggle_edit(self, checked: bool) -> None:
        if checked:
            # Can't edit while viewing source
            if self._viewing_source:
                self._edit_btn.blockSignals(True)
                self._edit_btn.setChecked(False)
                self._edit_btn.blockSignals(False)
                return
            self._browser.hide()
            self._editor.show()
            self._editor.setFocus()
        else:
            self._raw_content = self._editor.toPlainText()
            self._editor.hide()
            self._browser.show()
            self._render()

    def _on_toggle_source(self, checked: bool) -> None:
        self._viewing_source = checked
        if checked:
            self._source_btn.setText("← Notes")
            # Exit edit mode first
            if self._edit_btn.isChecked():
                self._edit_btn.setChecked(False)
            self._edit_btn.setEnabled(False)
            self._render_source()
        else:
            self._source_btn.setText("Source Text")
            self._edit_btn.setEnabled(bool(self._raw_content))
            self._render()

    def _on_text_changed(self) -> None:
        if not self._dirty:
            self._dirty = True
            self._update_file_label()

    def _on_save(self) -> None:
        if self._viewing_source:
            return
        if self._edit_btn.isChecked():
            self._raw_content = self._editor.toPlainText()
        if self._current_file:
            try:
                self._current_file.write_text(self._raw_content, encoding="utf-8")
                self._dirty = False
                self._update_file_label()
            except OSError as exc:
                QMessageBox.critical(self, "Save Failed", str(exc))
        else:
            self._save_as()

    def _on_read_aloud(self) -> None:
        text = self._raw_source if self._viewing_source else self._raw_content
        voice_id = VOICES[self._voice_combo.currentText()]
        rate = SPEEDS[self._speed_combo.currentText()]
        volume = VOLUMES[self._volume_combo.currentText()]
        self._tts_worker = TTSWorker(text, voice=voice_id, rate=rate, volume=volume)
        self._tts_worker.status.connect(self._on_tts_status)
        self._tts_worker.finished.connect(self._on_tts_finished)
        self._tts_worker.error.connect(self._on_tts_error)
        self._tts_worker.start()
        self._read_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

    def _on_stop_tts(self) -> None:
        self._stop_tts()

    def _on_tts_status(self, msg: str) -> None:
        self.tts_status.emit(msg)

    def _on_tts_finished(self) -> None:
        active_text = self._raw_source if self._viewing_source else self._raw_content
        self._read_btn.setEnabled(bool(active_text.strip()))
        self._stop_btn.setEnabled(False)
        self._tts_worker = None

    def _on_tts_error(self, msg: str) -> None:
        QMessageBox.warning(self, "TTS Error", msg)
        self._on_tts_finished()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _stop_tts(self) -> None:
        if self._tts_worker and self._tts_worker.isRunning():
            self._tts_worker.stop()
            self._tts_worker.wait()
        self._tts_worker = None
        active_text = self._raw_source if self._viewing_source else self._raw_content
        self._read_btn.setEnabled(bool(active_text.strip()))
        self._stop_btn.setEnabled(False)

    def _exit_source_view(self) -> None:
        if self._viewing_source:
            self._source_btn.blockSignals(True)
            self._source_btn.setChecked(False)
            self._source_btn.blockSignals(False)
            self._source_btn.setText("Source Text")
            self._viewing_source = False

    def _save_as(self) -> None:
        default_name = f"notes-{date.today()}.md"
        start = f"{self._last_save_dir}/{default_name}" if self._last_save_dir else default_name
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Notes", start, "Markdown Files (*.md)"
        )
        if not path:
            return
        try:
            Path(path).write_text(self._raw_content, encoding="utf-8")
            self._current_file = Path(path)
            self._last_save_dir = str(Path(path).parent)
            self._dirty = False
            self._update_file_label()
        except OSError as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))

    def _render(self) -> None:
        html_body = md.markdown(self._raw_content, extensions=["extra", "nl2br"])
        self._browser.setHtml(
            f"<html><head>{_build_css()}</head><body>{html_body}</body></html>"
        )

    def _render_source(self) -> None:
        escaped = (
            self._raw_source
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        self._browser.setHtml(
            f"<html><head>{_build_css()}</head>"
            f"<body><pre>{escaped}</pre></body></html>"
        )

    def _load_into_editor(self, content: str) -> None:
        self._editor.blockSignals(True)
        self._editor.setPlainText(content)
        self._editor.blockSignals(False)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self.save_btn.setEnabled(enabled)
        self._copy_btn.setEnabled(enabled)
        self._edit_btn.setEnabled(enabled)
        self._read_btn.setEnabled(enabled)

    def _update_file_label(self) -> None:
        if self._current_file:
            prefix = "● " if self._dirty else ""
            self._file_label.setText(f"{prefix}{self._current_file.name}")
        else:
            self._file_label.setText("Notes")
