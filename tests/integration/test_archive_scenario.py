"""
Integration: archive-related scenarios with real in-memory repos.
"""
import pytest
from storage.memory.shopping_list_repo import InMemoryShoppingListRepository
from storage.memory.shopping_item_repo import InMemoryShoppingItemRepository
from services.shopping_list_service import ShoppingListService
from services.shopping_item_service import ShoppingItemService
from services.sort_strategies import AlphabeticalSortStrategy
from services.observer import ShoppingListSubject, NotificationLog, ListCompletionObserver
from models.enums import ListStatus
from utils.exceptions import ListArchivedError, ShoppingListNotFoundError


def _make_services():
    list_repo = InMemoryShoppingListRepository()
    item_repo = InMemoryShoppingItemRepository()
    subject = ShoppingListSubject()
    subject.subscribe(ListCompletionObserver(NotificationLog()))
    list_svc = ShoppingListService(list_repo, item_repo, subject)
    item_svc = ShoppingItemService(item_repo, AlphabeticalSortStrategy())
    return list_svc, item_svc, list_repo


# ── archive basics ────────────────────────────────────────────────────────────

def test_archive_list_changes_status():
    list_svc, _, list_repo = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.archive_list("l1")
    sl = list_repo.get_by_id("l1")
    assert sl.status == ListStatus.ARCHIVED


def test_archive_list_is_archived_property_true():
    list_svc, _, list_repo = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.archive_list("l1")
    sl = list_repo.get_by_id("l1")
    assert sl.is_archived is True


def test_active_list_is_active_property_true():
    list_svc, _, list_repo = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    sl = list_repo.get_by_id("l1")
    assert sl.is_active is True


def test_archive_nonexistent_list_raises():
    list_svc, *_ = _make_services()
    with pytest.raises(ShoppingListNotFoundError):
        list_svc.archive_list("ghost")


def test_archive_already_archived_raises():
    list_svc, *_ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.archive_list("l1")
    with pytest.raises(ListArchivedError):
        list_svc.archive_list("l1")


# ── cannot add items to archived list ─────────────────────────────────────────

def test_archived_list_cannot_accept_new_items():
    list_svc, *_ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.archive_list("l1")
    with pytest.raises(ListArchivedError):
        list_svc.add_item("l1", "i1", "Milk", 1.0)


def test_active_list_accepts_items_before_archive():
    list_svc, item_svc, _ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.archive_list("l1")
    assert len(item_svc.get_items_sorted("l1")) == 1


def test_archived_list_rejects_add_after_items_were_added():
    list_svc, *_ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.archive_list("l1")
    with pytest.raises(ListArchivedError):
        list_svc.add_item("l1", "i2", "Bread", 1.0)


def test_adding_to_archived_error_message_contains_list_id():
    list_svc, *_ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.archive_list("l1")
    with pytest.raises(ListArchivedError, match="l1"):
        list_svc.add_item("l1", "i1", "Milk", 1.0)


# ── archived list still visible in owner query ────────────────────────────────

def test_archived_list_still_returned_by_get_lists_by_owner():
    list_svc, _, list_repo = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.archive_list("l1")
    lists = list_svc.get_lists_by_owner("u1")
    assert len(lists) == 1
    assert lists[0].status == ListStatus.ARCHIVED


def test_owner_has_both_active_and_archived_lists():
    list_svc, _, list_repo = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.create_list("l2", "Monthly", "u1")
    list_svc.archive_list("l1")
    lists = list_svc.get_lists_by_owner("u1")
    statuses = {sl.status for sl in lists}
    assert ListStatus.ACTIVE in statuses
    assert ListStatus.ARCHIVED in statuses


# ── items on archived list still readable ─────────────────────────────────────

def test_items_on_archived_list_still_readable():
    list_svc, item_svc, _ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    list_svc.archive_list("l1")
    items = item_svc.get_items_sorted("l1")
    assert len(items) == 2


def test_items_on_archived_list_can_still_be_purchased():
    list_svc, item_svc, _ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.archive_list("l1")
    item_svc.mark_purchased("i1")
    items = item_svc.get_items_sorted("l1")
    assert items[0].is_purchased is True


def test_items_on_archived_list_can_be_removed():
    list_svc, item_svc, _ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.archive_list("l1")
    list_svc.remove_item("i1")
    assert item_svc.get_items_sorted("l1") == []


# ── multiple lists: archive one, other unaffected ────────────────────────────

def test_archiving_one_list_does_not_affect_another():
    list_svc, item_svc, _ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.create_list("l2", "Monthly", "u1")
    list_svc.archive_list("l1")
    # l2 should still accept items
    list_svc.add_item("l2", "i1", "Milk", 1.0)
    assert len(item_svc.get_items_sorted("l2")) == 1


def test_archive_returns_updated_list_object():
    list_svc, *_ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    result = list_svc.archive_list("l1")
    assert result.status == ListStatus.ARCHIVED


def test_archive_error_is_value_error_subclass():
    list_svc, *_ = _make_services()
    list_svc.create_list("l1", "Weekly", "u1")
    list_svc.archive_list("l1")
    with pytest.raises(ValueError):
        list_svc.archive_list("l1")


def test_archive_not_found_error_is_key_error_subclass():
    list_svc, *_ = _make_services()
    with pytest.raises(KeyError):
        list_svc.archive_list("ghost")
