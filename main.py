import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QListWidget, QStackedWidget, QLabel, QTableView, QHeaderView
)
from PySide6.QtCore import Qt, QAbstractTableModel


class OrdersModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.headers = ["Order number", "Client", "Route", "Status"]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TMS - szkielet")
        self.resize(900, 600)

        # kontener centralny
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # boczne menu
        self.menu = QListWidget()
        self.menu.addItems(["Zlecenia", "Pojazdy", "Kierowcy"])
        self.menu.setFixedWidth(150)

        # obszar z widokami
        self.views = QStackedWidget()

        # --- widok Zlecenia jako tabela ---
        orders_data = [
            ["ZL/001", "Firma A", "Warszawa - Kraków", "W trakcie"],
            ["ZL/002", "Firma B", "Poznań - Gdańsk", "Zaplanowane"],
            ["ZL/003", "Firma C", "Wrocław - Łódź", "Zakończone"],
        ]

        self.orders_view = QTableView()
        self.orders_model = OrdersModel(orders_data)
        self.orders_view.setModel(self.orders_model)
        self.orders_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.views.addWidget(self.orders_view)
        self.views.addWidget(QLabel("Widok: Pojazdy"))
        self.views.addWidget(QLabel("Widok: Kierowcy"))

        layout.addWidget(self.menu)
        layout.addWidget(self.views)

        # sygnał -> slot: kliknięcie w menu przełącza widok
        self.menu.currentRowChanged.connect(self.views.setCurrentIndex)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())