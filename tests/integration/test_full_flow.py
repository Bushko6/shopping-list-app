"""
Integration: full end-to-end workflows with real in-memory repos and services.
No mocks — every component is wired together as in production.
"""
import pytest
from unittest.mock import MagicMock
from services.observer import (
    ShoppingListSubject,
    NotificationLog,
    ListCompletionObserver,
    ItemEvent,
    EventType,
)
from services.shopping_list_service import ShoppingListService
from services.shopping_item_service import ShoppingItemService
from services.notification_service import NotificationService
from services.sort_strategies import AlphabeticalSortStrategy
from storage.memory.shopping_list_repo import InMemoryShoppingListRepository
from storage.memory.shopping_item_repo import InMemoryShoppingItemRepository
from utils.exceptions import (
    ShoppingListNotFoundError,
    ShoppingItemNotFoundError,
    ListArchivedError,
    ItemAlreadyPurchasedError,
    ItemNotPurchasedError,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _wire():
    """Return a fully wired set of real services sharing the same repos."""
    list_repo = InMemoryShoppingListRepository()
    item_repo = InMemoryShoppingItemRepository()
    log = NotificationLog()
    subject = ShoppingListSubject()
    subject.subscribe(ListCompletionObserver(log))
    list_svc = ShoppingListService(list_repo, item_repo, subject)
    item_svc = ShoppingItemService(item_repo, AlphabeticalSortStrategy(), subject)
    notif_svc = NotificationService(log)
    return list_svc, item_svc, notif_svc, subject, log


# ── create / retrieve ─────────────────────────────────────────────────────────

def test_create_list_and_retrieve_by_owner():
    list_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    lists = list_svc.get_lists_by_owner("u1")
    assert len(lists) == 1
    assert lists[0].name == "Weekly"


def test_create_multiple_lists_same_owner():
    list_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.create_list("l2", "Monthly", "u1")
    assert len(list_svc.get_lists_by_owner("u1")) == 2


def test_create_lists_different_owners_isolated():
    list_svc, *_ = _wire()
    list_svc.create_list("l1", "Alice's list", "u1")
    list_svc.create_list("l2", "Bob's list", "u2")
    assert len(list_svc.get_lists_by_owner("u1")) == 1
    assert len(list_svc.get_lists_by_owner("u2")) == 1


def test_unknown_owner_returns_empty_list():
    list_svc, *_ = _wire()
    assert list_svc.get_lists_by_owner("nobody") == []


# ── add item ──────────────────────────────────────────────────────────────────

def test_add_item_to_list_stores_item():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 2.0)
    items = item_svc.get_items_sorted("l1")
    assert len(items) == 1
    assert items[0].name == "Milk"


def test_add_multiple_items_all_stored():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 2.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    list_svc.add_item("l1", "i3", "Eggs", 12.0)
    assert len(item_svc.get_items_sorted("l1")) == 3


def test_add_item_to_nonexistent_list_raises():
    list_svc, *_ = _wire()
    with pytest.raises(ShoppingListNotFoundError):
        list_svc.add_item("ghost", "i1", "Milk", 1.0)


def test_add_item_fires_item_added_event():
    list_svc, item_svc, notif_svc, subject, _ = _wire()
    captured = []
    mock_obs = MagicMock()
    mock_obs.on_event.side_effect = lambda e: captured.append(e)
    subject.subscribe(mock_obs)
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    assert any(e.type == EventType.ITEM_ADDED for e in captured)


def test_add_item_with_optional_fields_stored_correctly():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 2.0, unit="L", category="Dairy", price=1.50)
    item = item_svc.get_items_sorted("l1")[0]
    assert item.unit == "L"
    assert item.category == "Dairy"
    assert item.price == 1.50


# ── remove item ───────────────────────────────────────────────────────────────

def test_remove_item_no_longer_in_list():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.remove_item("i1")
    assert item_svc.get_items_sorted("l1") == []


def test_remove_nonexistent_item_raises():
    list_svc, *_ = _wire()
    with pytest.raises(ShoppingItemNotFoundError):
        list_svc.remove_item("ghost")


def test_remove_item_fires_item_removed_event():
    list_svc, item_svc, notif_svc, subject, _ = _wire()
    captured = []
    mock_obs = MagicMock()
    mock_obs.on_event.side_effect = lambda e: captured.append(e)
    subject.subscribe(mock_obs)
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    captured.clear()
    list_svc.remove_item("i1")
    assert any(e.type == EventType.ITEM_REMOVED for e in captured)


def test_remove_one_of_many_leaves_rest():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    list_svc.remove_item("i1")
    items = item_svc.get_items_sorted("l1")
    assert len(items) == 1
    assert items[0].id == "i2"


# ── completion observer ───────────────────────────────────────────────────────

def test_all_purchased_triggers_list_completed_event():
    list_svc, item_svc, notif_svc, subject, _ = _wire()
    captured = []
    mock_obs = MagicMock()
    mock_obs.on_event.side_effect = lambda e: captured.append(e)
    subject.subscribe(mock_obs)
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    item_svc.mark_purchased("i1")
    item_svc.mark_purchased("i2")
    assert any(e.type == EventType.LIST_COMPLETED for e in captured)


def test_list_completed_notification_logged():
    list_svc, item_svc, notif_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    item_svc.mark_purchased("i1")
    item_svc.mark_purchased("i2")
    notifications = notif_svc.get_notifications("l1")
    assert len(notifications) == 1
    assert "l1" in notifications[0]


def test_partial_purchase_no_list_completed_notification():
    list_repo = InMemoryShoppingListRepository()
    item_repo = InMemoryShoppingItemRepository()
    log = NotificationLog()
    subject = ShoppingListSubject()
    subject.subscribe(ListCompletionObserver(log))
    list_svc = ShoppingListService(list_repo, item_repo, subject)

    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    assert log.get_notifications("l1") == []


def test_empty_list_after_remove_no_completion():
    list_repo = InMemoryShoppingListRepository()
    item_repo = InMemoryShoppingItemRepository()
    log = NotificationLog()
    subject = ShoppingListSubject()
    subject.subscribe(ListCompletionObserver(log))
    list_svc = ShoppingListService(list_repo, item_repo, subject)

    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.remove_item("i1")
    # Empty list — _check_completion returns without firing LIST_COMPLETED
    assert log.get_notifications("l1") == []


# ── mark / unmark purchased via item_svc ─────────────────────────────────────

def test_mark_purchased_updates_item():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    item_svc.mark_purchased("i1")
    items = item_svc.get_items_sorted("l1")
    assert items[0].is_purchased is True


def test_mark_purchased_already_purchased_raises():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    item_svc.mark_purchased("i1")
    with pytest.raises(ItemAlreadyPurchasedError):
        item_svc.mark_purchased("i1")


def test_unmark_purchased_restores_item():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    item_svc.mark_purchased("i1")
    item_svc.unmark_purchased("i1")
    items = item_svc.get_items_sorted("l1")
    assert items[0].is_purchased is False
    assert items[0].purchased_at is None


def test_unmark_not_purchased_raises():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    with pytest.raises(ItemNotPurchasedError):
        item_svc.unmark_purchased("i1")


def test_get_unpurchased_returns_only_unpurchased():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    item_svc.mark_purchased("i1")
    unpurchased = item_svc.get_unpurchased("l1")
    assert len(unpurchased) == 1
    assert unpurchased[0].id == "i2"


def test_bulk_mark_purchased_marks_all_in_list():
    list_svc, item_svc, notif_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    list_svc.add_item("l1", "i3", "Eggs", 1.0)
    result = item_svc.bulk_mark_purchased("l1")
    assert len(result) == 3
    assert all(i.is_purchased for i in item_svc.get_items_sorted("l1"))
    assert len(notif_svc.get_notifications("l1")) == 1


def test_bulk_mark_purchased_only_marks_unpurchased():
    list_svc, item_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    item_svc.mark_purchased("i1")
    result = item_svc.bulk_mark_purchased("l1")
    assert len(result) == 1
    assert result[0].id == "i2"


# ── notification service ──────────────────────────────────────────────────────

def test_notification_service_returns_messages_for_list():
    list_svc, item_svc, notif_svc, *_ = _wire()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    item_svc.mark_purchased("i1")
    item_svc.mark_purchased("i2")
    msgs = notif_svc.get_notifications("l1")
    assert len(msgs) == 1
    assert "l1" in msgs[0]


def test_notification_service_all_notifications_empty_initially():
    _, _, notif_svc, *_ = _wire()
    assert notif_svc.get_all_notifications() == {}


def test_notification_service_unknown_list_returns_empty():
    _, _, notif_svc, *_ = _wire()
    assert notif_svc.get_notifications("unknown") == []
