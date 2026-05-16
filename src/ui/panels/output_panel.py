from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class OutputPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # --- Header row ---
        header_row = QHBoxLayout()

        header = QLabel("Notes")
        header.setStyleSheet("font-weight: bold; font-size: 15px;")

        self.save_btn = QPushButton("Save as Markdown")
        self.save_btn.setEnabled(False)

        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(self.save_btn)

        layout.addLayout(header_row)

        # --- Text area ---
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText(
            "Processed notes will appear here in markdown format.\n\n"
            "Add a URL or HTML file on the left, then press Process."
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
