import sqlite3

DB_PATH = "tms.db"

DRIVERS_HEADERS = ["ID", "Imię i nazwisko", "Numer prawa jazdy", "Numer telefonu"]

TRUCKS_HEADERS = ["ID", "Numer rejestracyjny", "Marka", "Model"]

ORDERS_HEADERS = ["ID", "Numer zlecenia", "Klient", "Kierowca", "Pojazd", "Trasa", "Stawka", "Status"]

CLIENTS_HEADERS = ["ID", "Nazwa firmy", "VAT EU", "Adres"]

COUNTRY_CODES = ["PL", "DE", "NL", "BE", "FR", "CZ", "SK", "AT", "IT", "ES"]
STATUS_COLORS = {
    "Nowe": "#E6F1FB",
    "W trakcie": "#FAEEDA",
    "Zakończone": "#E1F5EE",
}
STATUS_OPTIONS = list(STATUS_COLORS.keys())

def get_db_data(query, params = ()):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()
    return [list(row) for row in rows]

def get_driver(driver_id):
    rows = get_db_data("SELECT full_name, license_number, phone FROM drivers WHERE id = ?", (driver_id,))
    return rows[0] if rows else None
    
def get_drivers():
    return get_db_data("SELECT id, full_name, license_number, phone FROM drivers")

def get_drivers_for_combo():
    return get_db_data("SELECT id, full_name FROM drivers")

def get_truck(truck_id):
    rows = get_db_data("SELECT plate_number, make, vehicle_model FROM trucks WHERE id = ?", (truck_id,))
    return rows[0] if rows else None

def get_trucks():
    return get_db_data("SELECT id, plate_number, make, vehicle_model FROM trucks")

def get_trucks_for_combo():
    return get_db_data("SELECT id, plate_number FROM trucks")

def get_orders():
    return get_db_data("""
            SELECT orders.id,
                   orders.order_number,
                   clients.name,
                   drivers.full_name,
                   trucks.plate_number,
                   GROUP_CONCAT(stops.country_code || stops.postal_code, ' -> ' ORDER BY stops.stop_type, stops.sequence),
                   orders.rate,
                   orders.status
            FROM orders
            JOIN clients ON orders.client_id = clients.id
            JOIN drivers ON orders.driver_id = drivers.id
            JOIN trucks ON orders.truck_id = trucks.id
            LEFT JOIN stops ON stops.order_id = orders.id
            GROUP BY orders.id
    """)

def get_clients():
    return get_db_data("SELECT id, name, tax_id, address FROM clients")

def get_clients_for_combo():
    return get_db_data("SELECT id, name FROM clients")

def get_client(client_id):
    rows = get_db_data("SELECT name, tax_id, address FROM clients WHERE id = ?", (client_id,))
    return rows[0] if rows else None

def save_db_data(query, params=()):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute(query, params)
    row_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return row_id


def add_driver(full_name, license_number, phone):
    return save_db_data("INSERT INTO drivers (full_name, license_number, phone) VALUES (?, ?, ?)",(full_name, license_number, phone))


def add_truck(plate_number, make, vehicle_model):
    return save_db_data("INSERT INTO trucks (plate_number, make, vehicle_model) VALUES (?, ?, ?)", (plate_number, make, vehicle_model))

def add_client(name, tax_id, address):
    return save_db_data("INSERT INTO clients (name, tax_id, address) VALUES (?, ?, ?)", (name, tax_id, address))

def update_driver(driver_id, full_name, license_number, phone):
    return save_db_data("UPDATE drivers SET full_name = ?, license_number = ?, phone = ? WHERE id = ?", (full_name, license_number, phone, driver_id))

def update_truck(truck_id, plate_number, make, vehicle_model):
    return save_db_data("UPDATE trucks SET plate_number = ?, make = ?, vehicle_model = ? WHERE id = ?", (plate_number, make, vehicle_model, truck_id))

def update_client(client_id, name, tax_id, address):
    return save_db_data("UPDATE clients SET name = ?, tax_id = ?, address = ? WHERE id = ?", (name, tax_id, address, client_id))

def delete_driver(driver_id):
    save_db_data("DELETE FROM drivers WHERE id = ?", (driver_id,))

def delete_truck(truck_id):
    save_db_data("DELETE FROM trucks WHERE id = ?", (truck_id,))

def delete_client(client_id):
    save_db_data("DELETE FROM clients WHERE id = ?", (client_id,))



def add_order(data):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute(
            "INSERT INTO orders (order_number, client_id, driver_id, truck_id, rate, status) VALUES (?, ?, ?, ?, ?, ?)",
                        (data['order_number'], data['client_id'], data['driver_id'], data['truck_id'], float(data['rate']), data['status']))
    order_id = cursor.lastrowid

    stops_data = []
    for stop in data["stops"]:
        stops_data.append((
            order_id,
            stop["stop_type"],
            stop["country_code"],
            stop["postal_code"],
            stop["city"],
            stop["address"],
            stop["stop_date"],
            stop["sequence"]
        ))

    cursor.executemany(
        "INSERT INTO stops (order_id, stop_type, country_code, postal_code, city, address, stop_date, sequence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        stops_data
    )
    
    connection.commit()
    connection.close()
    return order_id

def get_order(order_id):
    rows = get_db_data("SELECT order_number, client_id, driver_id, truck_id, rate, status FROM orders WHERE id = ?", (order_id, ))
    return rows[0] if rows else None

def get_stops_for_order(order_id):
    return get_db_data("SELECT stop_type, sequence, country_code, postal_code, city, address, stop_date FROM stops WHERE order_id = ? ORDER BY stop_type, sequence", (order_id, ))

def update_order(order_id, data):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("UPDATE orders SET order_number = ?, client_id = ?, driver_id = ?, truck_id = ?, rate = ?, status = ? WHERE id = ?",
                    (data['order_number'], data['client_id'], data['driver_id'], data['truck_id'], float(data['rate']), data['status'], order_id))
    
    cursor.execute("DELETE FROM stops WHERE order_id = ?", (order_id,))

    stops_data = []
    for stop in data["stops"]:
        stops_data.append((
            order_id,
            stop["stop_type"],
            stop["country_code"],
            stop["postal_code"],
            stop["city"],
            stop["address"],
            stop["stop_date"],
            stop["sequence"]
        ))   

    cursor.executemany(
        "INSERT INTO stops (order_id, stop_type, country_code, postal_code, city, address, stop_date, sequence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        stops_data
    )
    connection.commit()
    connection.close()

def delete_order(order_id):
    save_db_data("DELETE FROM orders WHERE id = ?", (order_id,))