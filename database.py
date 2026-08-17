import sqlite3

DB_PATH = "tms.db"

DRIVERS_HEADERS = ["Imię i nazwisko", "Numer prawa jazdy", "Numer telefonu"]

TRUCKS_HEADERS = ["Numer rejestracyjny", "Marka", "Model"]

ORDERS_HEADERS = ["Numer zlecenia", "Klient", "Kierowca", "Pojazd", "Trasa", "Stawka", "Status"]

def get_drivers():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT full_name, license_number, phone FROM drivers")
    rows = cursor.fetchall()
    connection.close()
    return [list(row) for row in rows]

def get_trucks():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT plate_number, make, vehicle_model FROM trucks")
    rows = cursor.fetchall()
    connection.close()
    return [list(row) for row in rows]

def get_orders():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("""
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
            JOIN stops ON stops.order_id = orders.id
            GROUP BY orders.id
    """)
    rows = cursor.fetchall()
    connection.close()
    return [list(row) for row in rows]

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
