import sqlite3
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QTableView, QHeaderView,
    QPushButton, QMessageBox,
)
from PySide6.QtCore import Qt, QDate

from models import TableModel
from dialogs import AddOrderDialog, AddRecordDialog


from database import (
    ORDERS_HEADERS, TRUCKS_HEADERS, DRIVERS_HEADERS, CLIENTS_HEADERS,
    COUNTRY_CODES,
    get_orders, get_trucks, get_drivers, get_clients,
    add_driver, add_truck, add_client, add_order,
    get_client, get_driver, get_truck, get_order, get_stops_for_order,
    update_client, update_driver, update_truck, update_order,
    delete_client, delete_driver, delete_truck, delete_order,
    
)

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
        self.views_dict = {}
        self.tables = {
            "orders": {
                "load": get_orders,
                "get": get_order,
                "save": add_order,
                "update": update_order,
                "delete": delete_order,
            },
            "trucks": {
                "load": get_trucks,
                "get": get_truck,
                "save": add_truck,
                "update": update_truck,
                "delete": delete_truck,
            },
            "drivers": {
                "load": get_drivers,
                "get": get_driver,
                "save": add_driver,
                "update": update_driver,
                "delete": delete_driver,
            },
            "clients": {
                "load": get_clients,
                "get": get_client,
                "save": add_client,
                "update": update_client,
                "delete": delete_client,
            },
        }

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
        header = view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        view.setColumnHidden(0, True)

        view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        self.models[name] = model
        self.views_dict[name] = view

        page = QWidget()
        page_layout = QVBoxLayout(page)

        button = QPushButton("Dodaj")
        if name == "orders":
            button.clicked.connect(lambda: self.add_order(name))
        else:
            button.clicked.connect(lambda: self.add_record(name, headers))

        edit_button = QPushButton("Edytuj")
        if name == "orders":
            edit_button.clicked.connect(lambda: self.edit_order(name))
        else:
            edit_button.clicked.connect(lambda: self.edit_record(name, headers))

        delete_button = QPushButton("Usuń")
        delete_button.clicked.connect(lambda: self.delete_record(name))

        page_layout.addWidget(button)
        page_layout.addWidget(edit_button)
        page_layout.addWidget(delete_button)
        page_layout.addWidget(view)

        view.setAlternatingRowColors(True)

        return page

    def add_record(self, name, headers):
        dialog = AddRecordDialog(headers[1:], self)
        if dialog.exec():
                dialog_data = dialog.get_data()
                try:
                    self.tables[name]["save"](*dialog_data)
                    self.models[name].set_data(self.tables[name]["load"]())
                except sqlite3.IntegrityError as e:
                    QMessageBox.warning(self, "Błąd zapisu", str(e))

    def add_order(self, name):
        dialog = AddOrderDialog(self)
        if dialog.exec():
            try:
                self.tables[name]["save"](dialog.get_data())
                self.models[name].set_data(self.tables[name]["load"]())
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", str(e))

    def edit_record(self, name, headers):
        index = self.views_dict[name].currentIndex()
        if not index.isValid():
            QMessageBox.information(self, "Brak zaznaczenia", "Zaznacz wiersz do edycji")
            return
        current_row = index.row()
        current_row_id = self.models[name].get_row_id(current_row)

        dialog = AddRecordDialog(headers[1:], self)
        dialog.setWindowTitle("Edycja rekordu")
        values = self.tables[name]["get"](current_row_id)
        if values:
            for field, value in zip(dialog.inputs, values):
                field.setText(value)
        if dialog.exec():
            try:
                self.tables[name]["update"](current_row_id, *dialog.get_data())
                self.models[name].set_data(self.tables[name]["load"]()) 
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", str(e))

    def delete_record(self, name):
        index = self.views_dict[name].currentIndex()
        if not index.isValid():
            QMessageBox.information(self, "Brak zaznaczenia", "Zaznacz wiersz do usunięcia")
            return
        current_row = index.row()
        current_row_id = self.models[name].get_row_id(current_row)
        if QMessageBox.question(self, "Potwierdzenie", "Czy na pewno chcesz usunąć pozycję?") == QMessageBox.StandardButton.Yes:
            try:
                self.tables[name]["delete"](current_row_id)
                self.models[name].set_data(self.tables[name]["load"]()) 
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", str(e))

    def edit_order(self, name):
        index = self.views_dict[name].currentIndex()
        if not index.isValid():
            QMessageBox.information(self, "Brak zaznaczenia", "Zaznacz wiersz do edycji")
            return
        current_row = index.row()
        order_id = self.models[name].get_row_id(current_row)
        dialog = AddOrderDialog(self, with_default_stops=False)
        dialog.setWindowTitle("Edycja zlecenia")
        order_number, client_id, driver_id, truck_id, rate, status = self.tables[name]["get"](order_id)
        dialog.order_number.setText(order_number)
        dialog.rate.setText(str(rate))
        dialog.status.setCurrentText(status)
        dialog.client.setCurrentIndex(dialog.client.findData(client_id))
        dialog.driver.setCurrentIndex(dialog.driver.findData(driver_id))
        dialog.truck.setCurrentIndex(dialog.truck.findData(truck_id))

        stops = get_stops_for_order(order_id)

        for stop_type, _, country_code, postal_code, city, address, stop_date in stops:
            dialog.add_stop(stop_type)
            fields = dialog.stops[-1]
            fields["country_code"].setCurrentText(country_code)
            fields["postal_code"].setText(postal_code)
            fields["city"].setText(city or "")
            fields["address"].setText(address or "")
            fields["stop_date"].setDate(QDate.fromString(stop_date, Qt.ISODate))

        if dialog.exec():
            try:
                self.tables[name]["update"](order_id, dialog.get_data())
                self.models[name].set_data(self.tables[name]["load"]())
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", str(e))