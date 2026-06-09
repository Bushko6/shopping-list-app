from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ShoppingItem:
    id: str
    list_id: str
    name: str
    quantity: float
    unit: str = ""
    category: str = ""
    price: float = 0.0
    is_purchased: bool = False
    added_at: datetime = field(default_factory=datetime.now)
    purchased_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id cannot be empty")
        if not self.list_id.strip():
            raise ValueError("list_id cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.price < 0:
            raise ValueError("price cannot be negative")
