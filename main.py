import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QStackedWidget, QLabel, QTableView, QHeaderView,
    QPushButton, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QMessageBox
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from sample_data import (
    ORDERS_DATA, ORDERS_HEADERS,
    TRUCKS_DATA, TRUCKS_HEADERS,
    DRIVERS_DATA, DRIVERS_HEADERS,
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


class AddOrderDialog(QDialog):
    def __init__(self, headers, parent = None):
        super().__init__(parent)
        self.setWindowTitle("New order")

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

        self.orders_view = self.create_table("orders", ORDERS_DATA, ORDERS_HEADERS)

        self.trucks_view = self.create_table("trucks", TRUCKS_DATA, TRUCKS_HEADERS)

        self.drivers_view = self.create_table("drivers", DRIVERS_DATA, DRIVERS_HEADERS)

        # dodajemy tabele do QStackedWidget

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

        page = QWidget()
        page_layout = QVBoxLayout(page)

        button = QPushButton("Dodaj")
        button.clicked.connect(lambda: self.add_record(name, headers))

        page_layout.addWidget(button)
        page_layout.addWidget(view)

        return page

    def add_record(self, name, headers):
        dialog = AddOrderDialog(headers, self)
        if dialog.exec():
            self.models[name].add_row(dialog.get_data())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())