import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QLabel, QTableView, QHeaderView,
    QPushButton, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QMessageBox, QComboBox, QGroupBox
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

from database import (
    ORDERS_HEADERS, TRUCKS_HEADERS, DRIVERS_HEADERS, CLIENTS_HEADERS,
    get_orders, get_trucks, get_drivers, get_clients,
    add_driver, add_truck, add_client, add_order,
    get_clients_for_combo, get_drivers_for_combo, get_trucks_for_combo
)

    #klasa tworząca model tabeli

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

        main_layout = QVBoxLayout(self)

        order_layout = QFormLayout()

        self.stops_layout = QVBoxLayout()
        self.stops = []
        self.country_code = QComboBox()
        self.postal_code = QLineEdit()
        self.address = QLineEdit()
        self.stop_date = QLineEdit()
        
        


        stop_button_layout = QHBoxLayout()
        loading_button = QPushButton("Dodaj załadunek")
        unloading_button = QPushButton("Dodaj rozładunek ")
        stop_button_layout.addWidget(loading_button)
        stop_button_layout.addWidget(unloading_button)



        self.order_number = QLineEdit()
        self.rate = QLineEdit()
        self.status = QLineEdit()
        self.client = QComboBox()
        self.driver = QComboBox()
        self.truck = QComboBox()

        order_layout.addRow("Numer zlecenia", self.order_number)
        order_layout.addRow("Stawka", self.rate)
        order_layout.addRow("Status", self.status)
        order_layout.addRow("Klient", self.client)
        order_layout.addRow("Kierowca", self.driver)
        order_layout.addRow("Auto", self.truck)

        for client_id, name in get_clients_for_combo():
            self.client.addItem(name, client_id)

        for truck_id, plate_number in get_trucks_for_combo():
            self.truck.addItem(plate_number, truck_id)

        for driver_id, full_name in get_drivers_for_combo():
            self.driver.addItem(full_name, driver_id)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        loading_button.clicked.connect(lambda: self.add_stop("load"))
        unloading_button.clicked.connect(lambda: self.add_stop("unload"))

        main_layout.addLayout(order_layout)
        main_layout.addLayout(self.stops_layout)
        main_layout.addLayout(stop_button_layout)  
        main_layout.addWidget(buttons)
     

    def get_data(self):
        return {
            "order_number": self.order_number.text(),
            "client_id": self.client.currentData(),
            "driver_id": self.driver.currentData(),
            "truck_id": self.truck.currentData(),
            "rate": self.rate.text(),
            "status": self.status.text(),
        }

    def add_stop(self, stop_type):
        box = QGroupBox("Załadunek 1")
        box_layout = QFormLayout(box)
        
        country_code = QComboBox()
        postal_code = QLineEdit()
        city = QLineEdit()
        address = QLineEdit()
        stop_date = QLineEdit()
        
        country_code.addItems(["PL", "DE", "NL", "BE", "FR", "CZ", "SK", "AT", "IT", "ES"])

        self.stops.append({
            "stop_type" : stop_type,
            "country_code" : country_code,
            "postal_code" : postal_code,
            "city" : city,
            "address" : address,
            "stop_date" : stop_date
        })
        box_layout.addRow("Kraj", country_code)
        box_layout.addRow("Kod pocztowy", postal_code)
        box_layout.addRow("Miasto", city)
        box_layout.addRow("Adres", address)
        box_layout.addRow("Data", stop_date)

        self.stops_layout.addWidget(box)

              



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