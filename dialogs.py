from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox, QMessageBox,
    QGroupBox, QDateEdit, QPushButton, QVBoxLayout, QHBoxLayout,
)
from PySide6.QtCore import QDate, Qt

from database import get_clients_for_combo, get_drivers_for_combo, get_trucks_for_combo

STOP_TYPE_NAMES = {
    "load": "Załadunek",
    "unload": "Rozładunek",
}

from database import COUNTRY_CODES, STATUS_OPTIONS


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

        self.loads_layout = QHBoxLayout()
        self.unloads_layout = QHBoxLayout()
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
        main_layout.addLayout(self.loads_layout)
        main_layout.addLayout(self.unloads_layout)
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

        box.setMaximumWidth(220)

        print(box.sizeHint().width())

        if stop_type == "load":
            self.loads_layout.addWidget(box)
        else:
            self.unloads_layout.addWidget(box)

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