from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtGui import QFont


class OutputPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self.save_btn.clicked.connect(self._on_save)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header = QLabel("Notes")
        header.setStyleSheet("font-weight: bold; font-size: 15px;")
        self.save_btn = QPushButton("Save as Markdown")
        self.save_btn.setEnabled(False)
        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(self.save_btn)
        layout.addLayout(header_row)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText(
            "Processed notes will appear here in markdown format.\n\n"
            "Add URLs or files on the left, then press Process."
        )
        self.text_area.setFont(QFont("Consolas", 11))
        self.text_area.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.text_area)

    def set_content(self, markdown: str) -> None:
        self.text_area.setPlainText(markdown)
        self.save_btn.setEnabled(bool(markdown.strip()))

    def clear(self) -> None:
        self.text_area.clear()
        self.save_btn.setEnabled(False)

    def _on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Notes", "notes.md", "Markdown Files (*.md)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_area.toPlainText())
        except OSError as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))
