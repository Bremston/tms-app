import sqlite3

DB_PATH = "tms.db"

DRIVERS_HEADERS = ["Imię i nazwisko", "Numer prawa jazdy", "Numer telefonu"]

TRUCKS_HEADERS = ["Numer rejestracyjny", "Marka", "Model"]

ORDERS_HEADERS = ["Numer zlecenia", "Klient", "Kierowca", "Pojazd", "Trasa", "Stawka", "Status"]

CLIENTS_HEADERS = ["Nazwa firmy", "VAT EU", "Adres"]
COUNTRY_CODES = ["PL", "DE", "NL", "BE", "FR", "CZ", "SK", "AT", "IT", "ES"]

def get_db_data(query):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    connection.close()
    return [list(row) for row in rows]


def get_drivers():
    return get_db_data("SELECT full_name, license_number, phone FROM drivers")

def get_drivers_for_combo():
    return get_db_data("SELECT id, full_name FROM drivers")

def get_trucks():
    return get_db_data("SELECT plate_number, make, vehicle_model FROM trucks")

def get_trucks_for_combo():
    return get_db_data("SELECT id, plate_number FROM trucks")

def get_orders():
    return get_db_data("""
            SELECT orders.order_number,
                   clients.name,
                   drivers.full_name,
                   trucks.plate_number,
                   GROUP_CONCAT(stops.country_code || stops.postal_code, ' -> '),
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
    return get_db_data("SELECT name, tax_id, address FROM clients")

def get_clients_for_combo():
    return get_db_data("SELECT id, name FROM clients")

def add_driver(full_name, license_number, phone):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
            "INSERT INTO drivers (full_name, license_number, phone) VALUES (?, ?, ?)",
            (full_name, license_number, phone))
  
    driver_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return driver_id

def add_truck(plate_number, make, vehicle_model):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
            "INSERT INTO trucks (plate_number, make, vehicle_model) VALUES (?, ?, ?)",
                        (plate_number, make, vehicle_model))
    driver_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return driver_id

def add_client(name, tax_id, address):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
            "INSERT INTO clients (name, tax_id, address) VALUES (?, ?, ?)",
                        (name, tax_id, address))
    client_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return client_id

def add_order(data):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
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


