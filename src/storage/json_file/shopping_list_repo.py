import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from storage.interfaces import ShoppingListRepository
from models.shopping_list import ShoppingList
from models.enums import ListStatus


class JsonFileShoppingListRepository(ShoppingListRepository):
    def __init__(self, file_path: str) -> None:
        self._path = Path(file_path)
        self._store: dict[str, ShoppingList] = {}
        if self._path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self._path.read_text())
        for d in data:
            sl = ShoppingList(
                id=d["id"],
                name=d["name"],
                owner_id=d["owner_id"],
                created_at=datetime.fromisoformat(d["created_at"]),
                status=ListStatus[d["status"]],
            )
            self._store[sl.id] = sl

    def _save(self) -> None:
        data = [
            {
                "id": sl.id,
                "name": sl.name,
                "owner_id": sl.owner_id,
                "created_at": sl.created_at.isoformat(),
                "status": sl.status.name,
            }
            for sl in self._store.values()
        ]
        self._path.write_text(json.dumps(data, indent=2))

    def add(self, shopping_list: ShoppingList) -> None:
        if shopping_list.id in self._store:
            raise ValueError(f"ShoppingList '{shopping_list.id}' already exists")
        self._store[shopping_list.id] = shopping_list
        self._save()

    def get_by_id(self, list_id: str) -> Optional[ShoppingList]:
        return self._store.get(list_id)

    def list_all(self) -> list[ShoppingList]:
        return list(self._store.values())

    def update(self, shopping_list: ShoppingList) -> None:
        if shopping_list.id not in self._store:
            raise KeyError(f"ShoppingList '{shopping_list.id}' not found")
        self._store[shopping_list.id] = shopping_list
        self._save()

    def delete(self, list_id: str) -> None:
        if list_id not in self._store:
            raise KeyError(f"ShoppingList '{list_id}' not found")
        del self._store[list_id]
        self._save()

    def find_by_owner(self, owner_id: str) -> list[ShoppingList]:
        return [sl for sl in self._store.values() if sl.owner_id == owner_id]
