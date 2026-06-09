from datetime import datetime
from storage.interfaces import ShoppingItemRepository
from models.shopping_item import ShoppingItem
from services.sort_strategies import SortStrategy
from utils.exceptions import ShoppingItemNotFoundError, ItemAlreadyPurchasedError, ItemNotPurchasedError


class ShoppingItemService:
    def __init__(
        self,
        item_repo: ShoppingItemRepository,
        sort_strategy: SortStrategy,
    ) -> None:
        self._item_repo = item_repo
        self._sort_strategy = sort_strategy

    def mark_purchased(self, item_id: str) -> ShoppingItem:
        item = self._item_repo.get_by_id(item_id)
        if item is None:
            raise ShoppingItemNotFoundError(f"ShoppingItem '{item_id}' not found")
        if item.is_purchased:
            raise ItemAlreadyPurchasedError(f"Item '{item_id}' is already purchased")
        item.is_purchased = True
        item.purchased_at = datetime.now()
        self._item_repo.update(item)
        return item

    def unmark_purchased(self, item_id: str) -> ShoppingItem:
        item = self._item_repo.get_by_id(item_id)
        if item is None:
            raise ShoppingItemNotFoundError(f"ShoppingItem '{item_id}' not found")
        if not item.is_purchased:
            raise ItemNotPurchasedError(f"Item '{item_id}' is not purchased")
        item.is_purchased = False
        item.purchased_at = None
        self._item_repo.update(item)
        return item

    def bulk_mark_purchased(self, list_id: str) -> list[ShoppingItem]:
        items = self._item_repo.find_by_list(list_id)
        marked = []
        for item in items:
            if not item.is_purchased:
                item.is_purchased = True
                item.purchased_at = datetime.now()
                self._item_repo.update(item)
                marked.append(item)
        return marked

    def get_items_sorted(self, list_id: str) -> list[ShoppingItem]:
        items = self._item_repo.find_by_list(list_id)
        return self._sort_strategy.sort(items)

    def get_unpurchased(self, list_id: str) -> list[ShoppingItem]:
        return self._item_repo.find_unpurchased_by_list(list_id)
