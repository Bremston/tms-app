from dataclasses import dataclass

@dataclass
class Driver:
    id: int | None
    full_name: str
    license_number: str
    phone: str