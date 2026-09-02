from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor

STATUS_COLORS = {
    "Nowe": "#E6F1FB",
    "W trakcie": "#FAEEDA",
    "Zakończone": "#E1F5EE",
}
STATUS_OPTIONS = list(STATUS_COLORS.keys())

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