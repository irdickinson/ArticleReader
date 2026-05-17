import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def _icon_path() -> str:
    """Locate icon whether running from source or PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent
    return str(base / "assets" / "icon.ico")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Article Reader")
    app.setWindowIcon(QIcon(_icon_path()))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
