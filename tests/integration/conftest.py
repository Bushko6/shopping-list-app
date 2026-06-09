import pytest
from storage.memory.shopping_list_repo import InMemoryShoppingListRepository
from storage.memory.shopping_item_repo import InMemoryShoppingItemRepository
from storage.memory.user_repo import InMemoryUserRepository
from storage.memory.category_repo import InMemoryCategoryRepository
from services.shopping_list_service import ShoppingListService
from services.shopping_item_service import ShoppingItemService
from services.persistence_service import PersistenceService
from services.notification_service import NotificationService
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
def user_repo():
    return InMemoryUserRepository()


@pytest.fixture
def category_repo():
    return InMemoryCategoryRepository()


@pytest.fixture
def log():
    return NotificationLog()


@pytest.fixture
def subject(log):
    s = ShoppingListSubject()
    s.subscribe(ListCompletionObserver(log))
    return s


@pytest.fixture
def list_svc(list_repo, item_repo, subject):
    return ShoppingListService(list_repo, item_repo, subject)


@pytest.fixture
def item_svc(item_repo):
    return ShoppingItemService(item_repo, AlphabeticalSortStrategy())


@pytest.fixture
def notification_svc(log):
    return NotificationService(log)
