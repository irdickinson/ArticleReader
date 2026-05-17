from datetime import date
from pathlib import Path

import markdown as md
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont, QKeySequence, QPalette, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
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
</style>"""


class OutputPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._raw_content = ""
        self._current_file: Path | None = None
        self._dirty = False
        self._last_save_dir = ""
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_file(self, path: str) -> None:
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
        self._render()
        self._update_file_label()
        has_content = bool(content.strip())
        self._set_buttons_enabled(has_content)

    def set_content(self, markdown: str, file_path: str = "") -> None:
        self._current_file = Path(file_path) if file_path else None
        self._dirty = False
        self._raw_content = markdown
        self._load_into_editor(markdown)
        self._render()
        self._update_file_label()
        has_content = bool(markdown.strip())
        self._set_buttons_enabled(has_content)

    def clear(self) -> None:
        self._raw_content = ""
        self._current_file = None
        self._dirty = False
        self._browser.clear()
        self._load_into_editor("")
        self._set_buttons_enabled(False)
        self._file_label.setText("Notes")

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        self._file_label = QLabel("Notes")
        self._file_label.setStyleSheet("font-weight: bold; font-size: 15px;")

        self._edit_btn = QToolButton()
        self._edit_btn.setText("Edit")
        self._edit_btn.setCheckable(True)
        self._edit_btn.setToolTip("Toggle edit mode (edits are saved with Ctrl+S)")
        self._edit_btn.setEnabled(False)

        self._copy_btn = QToolButton()
        self._copy_btn.setText("Copy")
        self._copy_btn.setToolTip("Copy raw markdown to clipboard")
        self._copy_btn.setEnabled(False)

        self.save_btn = QPushButton("Save")
        self.save_btn.setEnabled(False)

        header_row.addWidget(self._file_label)
        header_row.addStretch()
        header_row.addWidget(self._edit_btn)
        header_row.addWidget(self._copy_btn)
        header_row.addWidget(self.save_btn)
        layout.addLayout(header_row)

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
        self._editor.textChanged.connect(self._on_text_changed)

        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self._on_save)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_copy(self) -> None:
        QApplication.clipboard().setText(self._raw_content)
        self._copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self._copy_btn.setText("Copy"))

    def _on_toggle_edit(self, checked: bool) -> None:
        if checked:
            self._browser.hide()
            self._editor.show()
            self._editor.setFocus()
        else:
            self._raw_content = self._editor.toPlainText()
            self._editor.hide()
            self._browser.show()
            self._render()

    def _on_text_changed(self) -> None:
        if not self._dirty:
            self._dirty = True
            self._update_file_label()

    def _on_save(self) -> None:
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

    def _load_into_editor(self, content: str) -> None:
        self._editor.blockSignals(True)
        self._editor.setPlainText(content)
        self._editor.blockSignals(False)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self.save_btn.setEnabled(enabled)
        self._copy_btn.setEnabled(enabled)
        self._edit_btn.setEnabled(enabled)

    def _update_file_label(self) -> None:
        if self._current_file:
            prefix = "● " if self._dirty else ""
            self._file_label.setText(f"{prefix}{self._current_file.name}")
        else:
            self._file_label.setText("Notes")
