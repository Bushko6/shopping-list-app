from typing import Optional
from storage.interfaces import ShoppingListRepository, ShoppingItemRepository
from models.shopping_list import ShoppingList
from models.shopping_item import ShoppingItem


class PersistenceService:
    def __init__(
        self,
        list_repo: ShoppingListRepository,
        item_repo: ShoppingItemRepository,
    ) -> None:
        self._list_repo = list_repo
        self._item_repo = item_repo

    def save_list(self, shopping_list: ShoppingList) -> ShoppingList:
        if self._list_repo.get_by_id(shopping_list.id) is None:
            self._list_repo.add(shopping_list)
        else:
            self._list_repo.update(shopping_list)
        return shopping_list

    def load_list(self, list_id: str) -> Optional[ShoppingList]:
        return self._list_repo.get_by_id(list_id)

    def save_item(self, item: ShoppingItem) -> ShoppingItem:
        if self._item_repo.get_by_id(item.id) is None:
            self._item_repo.add(item)
        else:
            self._item_repo.update(item)
        return item

    def load_item(self, item_id: str) -> Optional[ShoppingItem]:
        return self._item_repo.get_by_id(item_id)
