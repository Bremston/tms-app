import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QListWidget, QStackedWidget, QLabel, QTableView, QHeaderView
)
from PySide6.QtCore import Qt, QAbstractTableModel


class TableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self.headers = headers

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
        self.menu.addItems(["Orders", "Trucks", "Drivers"])
        self.menu.setFixedWidth(150)

        # obszar z widokami
        self.views = QStackedWidget()

        self.models = {}

        # --- widok Zlecenia jako tabela ---

        self.orders_view = self.create_table("orders", [
            ["ZL/001", "Firma A", "Warszawa - Kraków", "W trakcie"],
            ["ZL/002", "Firma B", "Poznań - Gdańsk", "Zaplanowane"],
            ["ZL/003", "Firma C", "Wrocław - Łódź", "Zakończone"],
        ], ["Order number", "Client", "Route", "Status"]
        )

        self.trucks_view = self.create_table("trucks", [
            ["PO 1234A", "Volvo", "FH16", "Marek Kowalski"],
            ["WA 5678B", "Scania", "R450", "Anna Nowak"],
            ["KR 9012C", "DAF", "XF 480", "Piotr Wiśniewski"],
            ["GD 3456D", "Mercedes-Benz", "Actros 1845", "Tomasz Lewandowski"],
            ["WR 7890E", "MAN", "TGX 18.500", "Katarzyna Dąbrowska"],
            ["PO 2468F", "Iveco", "S-Way 480", "Michał Zieliński"],
        ], ["Plate", "Make", "Model", "Driver"])

        self.drivers_view = self.create_table("drivers", [
            ["Marek Kowalski", "PL/1234567/01", "601 234 567", "W trasie"],
            ["Anna Nowak", "PL/2345678/02", "602 345 678", "Dostępny"],
            ["Piotr Wiśniewski", "PL/3456789/03", "603 456 789", "W trasie"],
            ["Tomasz Lewandowski", "PL/4567890/04", "604 567 890", "Urlop"],
            ["Katarzyna Dąbrowska", "PL/5678901/05", "605 678 901", "Dostępny"],
            ["Michał Zieliński", "PL/6789012/06", "606 789 012", "W trasie"],
        ], ["Full name", "License number", "Phone number", "Status"])



        self.views.addWidget(self.orders_view)
        self.views.addWidget(self.trucks_view)
        self.views.addWidget(self.drivers_view)

        layout.addWidget(self.menu)
        layout.addWidget(self.views)

        # sygnał -> slot: kliknięcie w menu przełącza widok
        self.menu.currentRowChanged.connect(self.views.setCurrentIndex)

    # metoda tworząca tabelę i przypisująca model do słownika
    def create_table(self, name, data, headers):
        view = QTableView()
        model = TableModel(data, headers)
        view.setModel(model)
        view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.models[name] = model
        return view

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())