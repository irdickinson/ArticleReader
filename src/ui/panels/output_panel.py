from datetime import date

import markdown as md
from PyQt6.QtGui import QFont, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def _build_css() -> str:
    """Generate CSS that matches the current app palette (light or dark)."""
    palette = QApplication.instance().palette()
    bg = palette.color(QPalette.ColorRole.Base)
    dark_mode = bg.lightness() < 128

    if dark_mode:
        text       = "#e8e8e8"
        muted      = "#b0b0b0"
        h1_border  = "#555"
        hr_color   = "#444"
        bq_border  = "#666"
        code_bg    = "#2c2c2c"
    else:
        text       = "#1a1a1a"
        muted      = "#555"
        h1_border  = "#ddd"
        hr_color   = "#e0e0e0"
        bq_border  = "#aaa"
        code_bg    = "#f4f4f4"

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
        self._last_save_dir = ""
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header row
        header_row = QHBoxLayout()
        header = QLabel("Notes")
        header.setStyleSheet("font-weight: bold; font-size: 15px;")

        self._raw_toggle = QCheckBox("Raw")
        self._raw_toggle.setToolTip("Toggle between rendered markdown and plain text")

        self.save_btn = QPushButton("Save as Markdown")
        self.save_btn.setEnabled(False)

        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(self._raw_toggle)
        header_row.addWidget(self.save_btn)
        layout.addLayout(header_row)

        # Rendered view (default)
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setPlaceholderText(
            "Processed notes will appear here.\n\n"
            "Add URLs or files on the left, then press Process."
        )
        layout.addWidget(self._browser)

        # Raw view (hidden by default)
        self._raw_view = QTextEdit()
        self._raw_view.setReadOnly(True)
        self._raw_view.setFont(QFont("Consolas", 11))
        self._raw_view.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._raw_view.hide()
        layout.addWidget(self._raw_view)

    def _connect_signals(self) -> None:
        self.save_btn.clicked.connect(self._on_save)
        self._raw_toggle.toggled.connect(self._on_toggle_raw)

    def set_content(self, markdown: str) -> None:
        self._raw_content = markdown
        self._render()
        self._raw_view.setPlainText(markdown)
        self.save_btn.setEnabled(bool(markdown.strip()))

    def clear(self) -> None:
        self._raw_content = ""
        self._browser.clear()
        self._raw_view.clear()
        self.save_btn.setEnabled(False)

    def _render(self) -> None:
        html_body = md.markdown(
            self._raw_content,
            extensions=["extra", "nl2br"],
        )
        css = _build_css()
        self._browser.setHtml(f"<html><head>{css}</head><body>{html_body}</body></html>")

    def _on_toggle_raw(self, checked: bool) -> None:
        if checked:
            self._browser.hide()
            self._raw_view.show()
        else:
            self._raw_view.hide()
            self._browser.show()

    def _on_save(self) -> None:
        default_name = f"notes-{date.today()}.md"
        start_path = f"{self._last_save_dir}/{default_name}" if self._last_save_dir else default_name
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Notes", start_path, "Markdown Files (*.md)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._raw_content)
            from pathlib import Path
            self._last_save_dir = str(Path(path).parent)
        except OSError as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))
