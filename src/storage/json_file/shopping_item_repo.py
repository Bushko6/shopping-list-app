import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from storage.interfaces import ShoppingItemRepository
from models.shopping_item import ShoppingItem


class JsonFileShoppingItemRepository(ShoppingItemRepository):
    def __init__(self, file_path: str) -> None:
        self._path = Path(file_path)
        self._store: dict[str, ShoppingItem] = {}
        if self._path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self._path.read_text())
        for d in data:
            purchased_at = (
                datetime.fromisoformat(d["purchased_at"])
                if d.get("purchased_at") is not None
                else None
            )
            item = ShoppingItem(
                id=d["id"],
                list_id=d["list_id"],
                name=d["name"],
                quantity=d["quantity"],
                unit=d.get("unit", ""),
                category=d.get("category", ""),
                price=d.get("price", 0.0),
                is_purchased=d.get("is_purchased", False),
                added_at=datetime.fromisoformat(d["added_at"]),
                purchased_at=purchased_at,
            )
            self._store[item.id] = item

    def _save(self) -> None:
        data = [
            {
                "id": i.id,
                "list_id": i.list_id,
                "name": i.name,
                "quantity": i.quantity,
                "unit": i.unit,
                "category": i.category,
                "price": i.price,
                "is_purchased": i.is_purchased,
                "added_at": i.added_at.isoformat(),
                "purchased_at": i.purchased_at.isoformat() if i.purchased_at else None,
            }
            for i in self._store.values()
        ]
        self._path.write_text(json.dumps(data, indent=2))

    def add(self, item: ShoppingItem) -> None:
        if item.id in self._store:
            raise ValueError(f"ShoppingItem '{item.id}' already exists")
        self._store[item.id] = item
        self._save()

    def get_by_id(self, item_id: str) -> Optional[ShoppingItem]:
        return self._store.get(item_id)

    def list_all(self) -> list[ShoppingItem]:
        return list(self._store.values())

    def update(self, item: ShoppingItem) -> None:
        if item.id not in self._store:
            raise KeyError(f"ShoppingItem '{item.id}' not found")
        self._store[item.id] = item
        self._save()

    def delete(self, item_id: str) -> None:
        if item_id not in self._store:
            raise KeyError(f"ShoppingItem '{item_id}' not found")
        del self._store[item_id]
        self._save()

    def find_by_list(self, list_id: str) -> list[ShoppingItem]:
        return [i for i in self._store.values() if i.list_id == list_id]

    def find_unpurchased_by_list(self, list_id: str) -> list[ShoppingItem]:
        return [i for i in self._store.values()
                if i.list_id == list_id and not i.is_purchased]
