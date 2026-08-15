import sqlite3

connection = sqlite3.connect("tms.db")
cursor = connection.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    tax_id TEXT,
    address TEXT
);

CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    license_number TEXT,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY,
    plate_number TEXT NOT NULL UNIQUE,
    make TEXT,
    vehicle_model TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    order_number TEXT NOT NULL UNIQUE,
    client_id INTEGER REFERENCES clients(id),
    driver_id INTEGER REFERENCES drivers(id),
    truck_id INTEGER REFERENCES trucks(id),
    rate REAL,
    status TEXT DEFAULT 'Nowe',
    notes TEXT,
    invoice_number TEXT
);

CREATE TABLE IF NOT EXISTS stops (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    stop_type TEXT NOT NULL CHECK (stop_type IN ('load', 'unload')),
    address TEXT NOT NULL,
    stop_date TEXT,
    sequence INTEGER NOT NULL DEFAULT 1
);
""")

cursor.executescript("""
DELETE FROM stops;
DELETE FROM orders;
DELETE FROM trucks;
DELETE FROM drivers;
DELETE FROM clients;
""")

cursor.executemany(
    "INSERT INTO drivers (full_name, license_number, phone) VALUES (?, ?, ?)",
    [("Marek Kowalski", "PL/1234567/01", "601 234 567"),
    ("Anna Nowak", "PL/2345678/02", "602 345 678")]
)

cursor.executemany(
    "INSERT INTO trucks (plate_number, make, vehicle_model) VALUES (?, ?, ?)",
    [("PO 1234A", "Volvo", "FH16"),
    ("WA 5678B", "Scania", "R450")]
)

cursor.executemany(
    "INSERT INTO clients (name, tax_id, address) VALUES (?, ?, ?)",
    [("Firma A", "PL1234567890", "Poznańska 1 Inowrocław 88-101"),
     ("Firma B", "PL1224567890", "Wrocławska 5 Inowrocław 88-101"),
     ("Firma C", "PL1214567890", "Warszawska 6 Inowrocław 88-101")]
)

cursor.execute("SELECT id FROM clients WHERE name = ?", ("Firma A",))
client_id = cursor.fetchone()[0]

cursor.execute("SELECT id FROM drivers WHERE full_name = ?", ("Marek Kowalski",))
driver_id = cursor.fetchone()[0]

cursor.execute("SELECT id FROM trucks WHERE plate_number = ?", ("WA 5678B",))
truck_id = cursor.fetchone()[0]

cursor.execute(
    "INSERT INTO orders (order_number, client_id, driver_id, truck_id, rate, status) VALUES (?, ?, ?, ?, ?, ?)",
    ("ZL/001", client_id, driver_id, truck_id, 450.0, "W trakcie")
)

cursor.execute("SELECT id FROM orders WHERE order_number = ?", ("ZL/001",))
order_id = cursor.fetchone()[0]

cursor.executemany(
    "INSERT INTO stops (order_id, stop_type, address, stop_date, sequence) VALUES (?, ?, ?, ?, ?)",
    [
        (order_id, "load", "Warszawa, Kolejowa 12", "2026-08-18", 1),
        (order_id, "unload", "Kraków, Wielicka 5", "2026-08-19", 1),
    ]
)

cursor.execute("""
    SELECT orders.order_number,
           clients.name,
           drivers.full_name,
           trucks.plate_number,
           orders.rate,
           orders.status
    FROM orders
    JOIN clients ON orders.client_id = clients.id
    JOIN drivers ON orders.driver_id = drivers.id
    JOIN trucks ON orders.truck_id = trucks.id
""")
cursor.execute("""
    SELECT orders.order_number,
       clients.name,
       GROUP_CONCAT(stops.address, ' → ') AS route
FROM orders
JOIN clients ON orders.client_id = clients.id
JOIN stops ON stops.order_id = orders.id
GROUP BY orders.id
""")

for row in cursor.fetchall():
    print(row)

connection.commit()
connection.close()