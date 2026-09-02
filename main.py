import sys
from PySide6.QtWidgets import QApplication

from main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    with open("style.qss", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
    window.show()
    sys.exit(app.exec())