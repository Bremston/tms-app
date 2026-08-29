import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QLabel, QTableView, QHeaderView,
    QPushButton, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QMessageBox, QComboBox, QGroupBox, QDateEdit
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QDate
from PySide6.QtGui import QColor

from database import (
    ORDERS_HEADERS, TRUCKS_HEADERS, DRIVERS_HEADERS, CLIENTS_HEADERS,
    COUNTRY_CODES,
    get_orders, get_trucks, get_drivers, get_clients,
    add_driver, add_truck, add_client, add_order,
    get_clients_for_combo, get_drivers_for_combo, get_trucks_for_combo,
    get_client, get_driver, get_truck, get_order, get_stops_for_order,
    update_client, update_driver, update_truck, update_order,
    delete_client, delete_driver, delete_truck, delete_order,
    
)

STATUS_COLORS = {
    "Nowe": "#E6F1FB",
    "W trakcie": "#FAEEDA",
    "Zakończone": "#E1F5EE",
}
STATUS_OPTIONS = list(STATUS_COLORS.keys())
STOP_TYPE_NAMES = {
    "load": "Załadunek",
    "unload": "Rozładunek",
}


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
        if role == Qt.BackgroundRole:
            if "Status" in self.headers:
                status_column = self.headers.index("Status")
                if index.column() == status_column:
                    status = self._data[index.row()][status_column]
                    color = STATUS_COLORS.get(status)
                    if color:
                        return QColor(color)

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

    def get_row_id(self, row):
        return self._data[row][0]

class AddRecordDialog(QDialog):
    def __init__(self, headers, values = None, parent = None):
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
    def __init__(self, parent = None, with_default_stops = True):
        super().__init__(parent)
        self.setWindowTitle("New order")

        main_layout = QVBoxLayout(self)

        order_layout = QFormLayout()

        self.stops_layout = QVBoxLayout()
        self.stops = []
        

        stop_button_layout = QHBoxLayout()
        loading_button = QPushButton("Dodaj załadunek")
        unloading_button = QPushButton("Dodaj rozładunek ")
        stop_button_layout.addWidget(loading_button)
        stop_button_layout.addWidget(unloading_button)

        loading_button.clicked.connect(lambda: self.add_stop("load"))
        unloading_button.clicked.connect(lambda: self.add_stop("unload"))


        self.order_number = QLineEdit()
        self.rate = QLineEdit()
        self.status = QComboBox()
        self.client = QComboBox()
        self.driver = QComboBox()
        self.truck = QComboBox()

        self.status.addItems(STATUS_OPTIONS)


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

        if with_default_stops:
            self.add_stop("load")
            self.add_stop("unload")

        main_layout.addLayout(order_layout)
        main_layout.addLayout(self.stops_layout)
        main_layout.addLayout(stop_button_layout)  
        main_layout.addWidget(buttons)
     

    def get_data(self):

        result = []
        counters = {"load" : 0, "unload" : 0}
        for stop in self.stops:
            counters[stop["stop_type"]] += 1
            result.append({
                "stop_type" : stop["stop_type"],
                "sequence" : counters[stop["stop_type"]],
                "country_code" : stop["country_code"].currentText(),
                "postal_code" : stop["postal_code"].text(),
                "city" : stop["city"].text(),
                "address" : stop["address"].text(),
                "stop_date" : stop["stop_date"].date().toString(Qt.ISODate)
            })

        return {
            "order_number": self.order_number.text(),
            "client_id": self.client.currentData(),
            "driver_id": self.driver.currentData(),
            "truck_id": self.truck.currentData(),
            "rate": float(self.rate.text().replace(",",".")),
            "status": self.status.currentText(),
            "stops" : result
        }
    
    def add_stop(self, stop_type):

        same_type_count = len([s for s in self.stops if s["stop_type"] == stop_type])
        
        word = "Załadunek" if stop_type == "load" else "Rozładunek"
        title = f"{word} {same_type_count + 1}"

        box = QGroupBox(title)
        box_layout = QFormLayout(box)


        country_code = QComboBox()
        postal_code = QLineEdit()
        city = QLineEdit()
        address = QLineEdit()
        stop_date = QDateEdit()

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

        country_code.addItems(COUNTRY_CODES)

        stop_date.setCalendarPopup(True)
        stop_date.setDate(QDate.currentDate())

        self.stops_layout.addWidget(box)

    def accept(self):
        if not self.order_number.text().strip():
            QMessageBox.warning(self, "Brak danych", "Wpisz numer zlecenia.")
            return
        try:
            float(self.rate.text().replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Błędna stawka", "Podaj stawkę jako liczbę.")
            return
        counters = {"load" : 0, "unload" : 0}
        for stop in self.stops:
            word = STOP_TYPE_NAMES[stop["stop_type"]]
            counters[stop["stop_type"]] += 1
            number = counters[stop['stop_type']]
            if not stop["postal_code"].text().strip():
                QMessageBox.warning(self, "Brak danych", f"{word} {number}: Brak kodu pocztowego")
                return
        if counters["load"] == 0:
            QMessageBox.warning(self, "Brak danych", "Uzupełnij załadunek")
            return
        if counters["unload"] == 0:
            QMessageBox.warning(self, "Brak danych", "Uzupełnij rozładunek")
            return
        super().accept()
        


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
        self.db_getters = {"drivers": get_driver, "trucks": get_truck, "clients": get_client, "orders" : get_order}
        self.db_updaters = {"drivers": update_driver, "trucks": update_truck, "clients": update_client, "orders" : update_order,}
        self.db_loaders = {"orders": get_orders, "drivers": get_drivers, "trucks": get_trucks, "clients": get_clients,}
        self.db_deleters = {"drivers" : delete_driver, "trucks" : delete_truck, "clients" : delete_client, "orders" : delete_order,}
        self.views_dict = {}
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
                    self.db_savers[name](*dialog_data)
                    self.models[name].set_data(self.db_loaders[name]())
                except sqlite3.IntegrityError as e:
                    QMessageBox.warning(self, "Błąd zapisu", str(e))

    def add_order(self, name):
        dialog = AddOrderDialog(self)
        if dialog.exec():
            try:
                self.db_savers[name](dialog.get_data())
                self.models[name].set_data(get_orders())
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
        values = self.db_getters[name](current_row_id)
        if values:
            for field, value in zip(dialog.inputs, values):
                field.setText(value)
        if dialog.exec():
            try:
                self.db_updaters[name](current_row_id, *dialog.get_data())
                self.models[name].set_data(self.db_loaders[name]()) 
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
                self.db_deleters[name](current_row_id)
                self.models[name].set_data(self.db_loaders[name]()) 
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
        order_number, client_id, driver_id, truck_id, rate, status = self.db_getters["orders"](order_id)
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
                self.db_updaters[name](order_id, dialog.get_data())
                self.models[name].set_data(self.db_loaders[name]())
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "Błąd zapisu", str(e))
                


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