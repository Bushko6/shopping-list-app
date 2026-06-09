from datetime import datetime
from storage.interfaces import ShoppingListRepository, ShoppingItemRepository
from models.shopping_list import ShoppingList
from models.shopping_item import ShoppingItem
from models.enums import ListStatus
from services.observer import ShoppingListSubject, ItemEvent, EventType
from utils.exceptions import ShoppingListNotFoundError, ShoppingItemNotFoundError, ListArchivedError


class ShoppingListService:
    def __init__(
        self,
        list_repo: ShoppingListRepository,
        item_repo: ShoppingItemRepository,
        subject: ShoppingListSubject,
    ) -> None:
        self._list_repo = list_repo
        self._item_repo = item_repo
        self._subject = subject

    def create_list(self, id: str, name: str, owner_id: str) -> ShoppingList:
        sl = ShoppingList(id=id, name=name, owner_id=owner_id,
                          created_at=datetime.now(), status=ListStatus.ACTIVE)
        self._list_repo.add(sl)
        return sl

    def archive_list(self, list_id: str) -> ShoppingList:
        sl = self._list_repo.get_by_id(list_id)
        if sl is None:
            raise ShoppingListNotFoundError(f"ShoppingList '{list_id}' not found")
        if sl.is_archived:
            raise ListArchivedError(f"ShoppingList '{list_id}' is already archived")
        sl.status = ListStatus.ARCHIVED
        self._list_repo.update(sl)
        return sl

    def get_lists_by_owner(self, owner_id: str) -> list[ShoppingList]:
        return self._list_repo.find_by_owner(owner_id)

    def add_item(self, list_id: str, item_id: str, name: str,
                 quantity: float, **kwargs) -> ShoppingItem:
        sl = self._list_repo.get_by_id(list_id)
        if sl is None:
            raise ShoppingListNotFoundError(f"ShoppingList '{list_id}' not found")
        if sl.is_archived:
            raise ListArchivedError(f"Cannot add items to archived list '{list_id}'")
        item = ShoppingItem(id=item_id, list_id=list_id, name=name,
                            quantity=quantity, added_at=datetime.now(), **kwargs)
        self._item_repo.add(item)
        self._subject.notify(ItemEvent(type=EventType.ITEM_ADDED,
                                       list_id=list_id, item_id=item_id))
        self._check_completion(list_id)
        return item

    def remove_item(self, item_id: str) -> None:
        item = self._item_repo.get_by_id(item_id)
        if item is None:
            raise ShoppingItemNotFoundError(f"ShoppingItem '{item_id}' not found")
        list_id = item.list_id
        self._item_repo.delete(item_id)
        self._subject.notify(ItemEvent(type=EventType.ITEM_REMOVED,
                                       list_id=list_id, item_id=item_id))
        self._check_completion(list_id)

    def _check_completion(self, list_id: str) -> None:
        remaining = self._item_repo.find_by_list(list_id)
        if remaining and all(i.is_purchased for i in remaining):
            self._subject.notify(ItemEvent(type=EventType.LIST_COMPLETED,
                                           list_id=list_id, item_id=None))
