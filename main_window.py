import sqlite3
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QTableView, QHeaderView,
    QPushButton, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, QDate, QSortFilterProxyModel

from models import TableModel
from dialogs import AddOrderDialog, AddRecordDialog
from config import TABLES

from database import ORDERS_HEADERS, TRUCKS_HEADERS, DRIVERS_HEADERS, CLIENTS_HEADERS, get_stops_for_order

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
        self.proxies = {}

        # --- widok Zlecenia jako tabela ---

        self.orders_view = self.create_table("orders", TABLES["orders"]["load"](), ORDERS_HEADERS)
        self.trucks_view = self.create_table("trucks", TABLES["trucks"]["load"](), TRUCKS_HEADERS)
        self.drivers_view = self.create_table("drivers", TABLES["drivers"]["load"](), DRIVERS_HEADERS)
        self.clients_view = self.create_table("clients", TABLES["clients"]["load"](), CLIENTS_HEADERS)

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
        header = view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)


        view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        self.models[name] = model
        self.views_dict[name] = view

        proxy = QSortFilterProxyModel()
        proxy.setSourceModel(model)
        view.setModel(proxy)
        view.setSortingEnabled(True)

        self.proxies[name] = proxy

        page = QWidget()
        page_layout = QVBoxLayout(page)
        interface_layout = QHBoxLayout()

        button = QPushButton("Dodaj")
        view.setColumnHidden(0, True)

        search_bar = QLineEdit()

        search_bar.textChanged.connect(proxy.setFilterFixedString)
        proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        proxy.setFilterKeyColumn(-1)

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

        page_layout.addLayout(interface_layout)
        interface_layout.addWidget(button)
        interface_layout.addWidget(edit_button)
        interface_layout.addWidget(delete_button)
        interface_layout.addStretch()
        interface_layout.addWidget(search_bar)
        # page_layout.addWidget(interface)
        page_layout.addWidget(view)

        view.setAlternatingRowColors(True)

        return page

    def add_record(self, name, headers):
        dialog = AddRecordDialog(headers[1:], self)
        if dialog.exec():
                dialog_data = dialog.get_data()
                try:
                    TABLES[name]["save"](*dialog_data)
                    self.models[name].set_data(TABLES[name]["load"]())
                except sqlite3.IntegrityError as e:
                    QMessageBox.warning(self, "Błąd zapisu", str(e))

    def add_order(self, name):
        dialog = AddOrderDialog(self)
        if dialog.exec():
            try:
                TABLES[name]["save"](dialog.get_data())
                self.models[name].set_data(TABLES[name]["load"]())
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", str(e))

    def edit_record(self, name, headers):
        index = self.views_dict[name].currentIndex()
        if not index.isValid():
            QMessageBox.information(self, "Brak zaznaczenia", "Zaznacz wiersz do edycji")
            return
        current_row = self.proxies[name].mapToSource(index).row()
        current_row_id = self.models[name].get_row_id(current_row)

        dialog = AddRecordDialog(headers[1:], self)
        dialog.setWindowTitle("Edycja rekordu")
        values = TABLES[name]["get"](current_row_id)
        if values:
            for field, value in zip(dialog.inputs, values):
                field.setText(value)
        if dialog.exec():
            try:
                TABLES[name]["update"](current_row_id, *dialog.get_data())
                self.models[name].set_data(TABLES[name]["load"]()) 
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", str(e))

    def delete_record(self, name):
        index = self.views_dict[name].currentIndex()
        if not index.isValid():
            QMessageBox.information(self, "Brak zaznaczenia", "Zaznacz wiersz do usunięcia")
            return
        current_row = self.proxies[name].mapToSource(index).row()
        current_row_id = self.models[name].get_row_id(current_row)
        if QMessageBox.question(self, "Potwierdzenie", "Czy na pewno chcesz usunąć pozycję?") == QMessageBox.StandardButton.Yes:
            try:
                TABLES[name]["delete"](current_row_id)
                self.models[name].set_data(TABLES[name]["load"]()) 
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", str(e))

    def edit_order(self, name):
        index = self.views_dict[name].currentIndex()
        if not index.isValid():
            QMessageBox.information(self, "Brak zaznaczenia", "Zaznacz wiersz do edycji")
            return
        current_row = self.proxies[name].mapToSource(index).row()
        order_id = self.models[name].get_row_id(current_row)
        dialog = AddOrderDialog(self, with_default_stops=False)
        dialog.setWindowTitle("Edycja zlecenia")
        order_number, client_id, driver_id, truck_id, rate, status = TABLES[name]["get"](order_id)
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
                TABLES[name]["update"](order_id, dialog.get_data())
                self.models[name].set_data(TABLES[name]["load"]())
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", str(e))