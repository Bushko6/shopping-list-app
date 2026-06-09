import pytest
from storage.memory.shopping_list_repo import InMemoryShoppingListRepository
from storage.memory.shopping_item_repo import InMemoryShoppingItemRepository
from services.shopping_list_service import ShoppingListService
from services.shopping_item_service import ShoppingItemService
from services.sort_strategies import AlphabeticalSortStrategy
from services.observer import (
    ShoppingListSubject,
    NotificationLog,
    ListCompletionObserver,
)


@pytest.fixture
def list_repo():
    return InMemoryShoppingListRepository()


@pytest.fixture
def item_repo():
    return InMemoryShoppingItemRepository()


@pytest.fixture
def log():
    return NotificationLog()


@pytest.fixture
def subject(log):
    s = ShoppingListSubject()
    s.subscribe(ListCompletionObserver(log))
    return s
