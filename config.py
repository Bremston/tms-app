from database import (
    ORDERS_HEADERS, TRUCKS_HEADERS, DRIVERS_HEADERS, CLIENTS_HEADERS,
    get_orders, get_trucks, get_drivers, get_clients,
    add_driver, add_truck, add_client, add_order,
    get_client, get_driver, get_truck, get_order, get_stops_for_order,
    update_client, update_driver, update_truck, update_order,
    delete_client, delete_driver, delete_truck, delete_order,
    
)


TABLES = {
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