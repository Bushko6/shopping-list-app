from dataclasses import dataclass, field
from datetime import datetime
from .enums import ListStatus


@dataclass
class ShoppingList:
    id: str
    name: str
    owner_id: str
    created_at: datetime = field(default_factory=datetime.now)
    status: ListStatus = field(default=ListStatus.ACTIVE)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty")

    @property
    def is_archived(self) -> bool:
        return self.status == ListStatus.ARCHIVED

    @property
    def is_active(self) -> bool:
        return self.status == ListStatus.ACTIVE
