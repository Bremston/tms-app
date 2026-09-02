import sys
from PySide6.QtWidgets import QApplication

from main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    app.setStyleSheet("""
    QListWidget {
        background: #f7f7f5;
        border: none;
        outline: none;
        font-size: 14px;
    }
    QListWidget::item {
        padding: 9px 16px;
        color: #6b6b66;
    }
    QListWidget::item:selected {
        background: #e6f1fb;
        color: #185fa5;
    }
    QPushButton {
        background: #378add;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
    }
    QPushButton:hover {
        background: #185fa5;
    }
    QHeaderView::section {
        background: #f1efe8;
        border: none;
        border-bottom: 1px solid #d3d1c7;
        padding: 10px;
        font-weight: 500;
    }
    QTableView {
        border: none;
    }
    """)
    window.show()
    sys.exit(app.exec())