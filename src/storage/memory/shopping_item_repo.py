from typing import Optional
from storage.interfaces import ShoppingItemRepository
from models.shopping_item import ShoppingItem


class InMemoryShoppingItemRepository(ShoppingItemRepository):
    def __init__(self) -> None:
        self._store: dict[str, ShoppingItem] = {}

    def add(self, item: ShoppingItem) -> None:
        if item.id in self._store:
            raise ValueError(f"ShoppingItem '{item.id}' already exists")
        self._store[item.id] = item

    def get_by_id(self, item_id: str) -> Optional[ShoppingItem]:
        return self._store.get(item_id)

    def list_all(self) -> list[ShoppingItem]:
        return list(self._store.values())

    def update(self, item: ShoppingItem) -> None:
        if item.id not in self._store:
            raise KeyError(f"ShoppingItem '{item.id}' not found")
        self._store[item.id] = item

    def delete(self, item_id: str) -> None:
        if item_id not in self._store:
            raise KeyError(f"ShoppingItem '{item_id}' not found")
        del self._store[item_id]

    def find_by_list(self, list_id: str) -> list[ShoppingItem]:
        return [i for i in self._store.values() if i.list_id == list_id]

    def find_unpurchased_by_list(self, list_id: str) -> list[ShoppingItem]:
        return [i for i in self._store.values()
                if i.list_id == list_id and not i.is_purchased]
