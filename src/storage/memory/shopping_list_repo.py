from typing import Optional
from storage.interfaces import ShoppingListRepository
from models.shopping_list import ShoppingList


class InMemoryShoppingListRepository(ShoppingListRepository):
    def __init__(self) -> None:
        self._store: dict[str, ShoppingList] = {}

    def add(self, shopping_list: ShoppingList) -> None:
        if shopping_list.id in self._store:
            raise ValueError(f"ShoppingList '{shopping_list.id}' already exists")
        self._store[shopping_list.id] = shopping_list

    def get_by_id(self, list_id: str) -> Optional[ShoppingList]:
        return self._store.get(list_id)

    def list_all(self) -> list[ShoppingList]:
        return list(self._store.values())

    def update(self, shopping_list: ShoppingList) -> None:
        if shopping_list.id not in self._store:
            raise KeyError(f"ShoppingList '{shopping_list.id}' not found")
        self._store[shopping_list.id] = shopping_list

    def delete(self, list_id: str) -> None:
        if list_id not in self._store:
            raise KeyError(f"ShoppingList '{list_id}' not found")
        del self._store[list_id]

    def find_by_owner(self, owner_id: str) -> list[ShoppingList]:
        return [sl for sl in self._store.values() if sl.owner_id == owner_id]
