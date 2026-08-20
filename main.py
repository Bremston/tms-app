import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QLabel, QTableView, QHeaderView,
    QPushButton, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

from database import (
    ORDERS_HEADERS, TRUCKS_HEADERS, DRIVERS_HEADERS, CLIENTS_HEADERS,
    get_orders, get_trucks, get_drivers, get_clients,
    add_driver, add_truck, add_client, add_order,
    get_clients_for_combo, get_drivers_for_combo, get_trucks_for_combo
)


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

    def add_row(self, row):
        position = len(self._data)
        self.beginInsertRows(QModelIndex(), position, position)
        self._data.append(row)
        self.endInsertRows()

    def set_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

class AddRecordDialog(QDialog):
    def __init__(self, headers, parent = None):
        super().__init__(parent)
        self.setWindowTitle("New record")

        layout = QFormLayout(self)
        self.inputs = []

        for header in headers:
            field = QLineEdit()
            layout.addRow(header, field)
            self.inputs.append(field)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return [field.text() for field in self.inputs]

    def accept(self):
        if any(not field.text().strip() for field in self.inputs):
            QMessageBox.warning(self, "Brak danych", "Wypełnij wszystkie pola.")
            return 
        super().accept()

class AddOrderDialog(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("New order")

        layout = QFormLayout(self)

        self.order_number = QLineEdit()
        self.rate = QLineEdit()
        self.status = QLineEdit()
        self.client = QComboBox()
        self.driver = QComboBox()
        self.truck = QComboBox()

        layout.addRow("Numer zlecenia", self.order_number)
        layout.addRow("Stawka", self.rate)
        layout.addRow("Status", self.status)
        layout.addRow("Klient", self.client)
        layout.addRow("Kierowca", self.driver)
        layout.addRow("Auto", self.truck)

        for client_id, name in get_clients_for_combo():
            self.client.addItem(name, client_id)

        for truck_id, plate_number in get_trucks_for_combo():
            self.truck.addItem(plate_number, truck_id)

        for driver_id, full_name in get_drivers_for_combo():
            self.driver.addItem(full_name, driver_id)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)        

    def get_data(self):
        return {
            "order_number": self.order_number.text(),
            "client_id": self.client.currentData(),
            "driver_id": self.driver.currentData(),
            "truck_id": self.truck.currentData(),
            "rate": self.rate.text(),
            "status": self.status.text(),
        }




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
        self.menu.addItems(["Zlecenia", "Pojazdy", "Kierowcy", "Klienci"])
        self.menu.setFixedWidth(150)

        # obszar z widokami
        self.views = QStackedWidget()

        self.models = {}
        self.db_savers = {"drivers" : add_driver, "trucks" : add_truck, "clients" : add_client, "orders" : add_order}

        # --- widok Zlecenia jako tabela ---

        self.orders_view = self.create_table("orders", get_orders(), ORDERS_HEADERS)
        self.trucks_view = self.create_table("trucks", get_trucks(), TRUCKS_HEADERS)
        self.drivers_view = self.create_table("drivers", get_drivers(), DRIVERS_HEADERS)
        self.clients_view = self.create_table("clients", get_clients(), CLIENTS_HEADERS)

        # dodajemy tabele do QStackedWidget

        self.views.addWidget(self.orders_view)
        self.views.addWidget(self.trucks_view)
        self.views.addWidget(self.drivers_view)
        self.views.addWidget(self.clients_view)

        layout.addWidget(self.menu)
        layout.addWidget(self.views)

        # sygnał -> slot: kliknięcie w menu przełącza widok
        self.menu.currentRowChanged.connect(self.views.setCurrentIndex)

    # metoda tworząca tabelę, przypisująca model do słownika
    def create_table(self, name, data, headers):
        view = QTableView()
        model = TableModel(data, headers)
        view.setModel(model)
        view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.models[name] = model

        page = QWidget()
        page_layout = QVBoxLayout(page)

        button = QPushButton("Dodaj")
        if name == "orders":
            button.clicked.connect(lambda: self.add_order(name))
        else:
            button.clicked.connect(lambda: self.add_record(name, headers))

        page_layout.addWidget(button)
        page_layout.addWidget(view)

        return page

    def add_record(self, name, headers):
        dialog = AddRecordDialog(headers, self)
        if dialog.exec():
                dialog_data = dialog.get_data()
                try:
                    self.db_savers[name](*dialog_data)
                    self.models[name].add_row(dialog_data)
                except sqlite3.IntegrityError as e:
                    QMessageBox.warning(self, "Błąd zapisu", e)

    def add_order(self, name):
        dialog = AddOrderDialog(self)
        if dialog.exec():
            try:
                self.db_savers[name](dialog.get_data())
                self.models[name].set_data(get_orders())
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", e)

                


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())