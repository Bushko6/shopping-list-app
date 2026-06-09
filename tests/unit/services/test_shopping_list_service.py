import pytest
from datetime import datetime
from unittest.mock import MagicMock, call
from models.shopping_list import ShoppingList
from models.shopping_item import ShoppingItem
from models.enums import ListStatus
from services.shopping_list_service import ShoppingListService
from services.observer import EventType


def _make_list(id="l1", owner_id="u1", status=ListStatus.ACTIVE):
    return ShoppingList(id=id, name="Weekly", owner_id=owner_id,
                        created_at=datetime(2025, 1, 1), status=status)


def _make_item(id="i1", list_id="l1", is_purchased=False):
    return ShoppingItem(id=id, list_id=list_id, name="Milk", quantity=1.0,
                        is_purchased=is_purchased, added_at=datetime(2025, 1, 1))


@pytest.fixture
def deps():
    return dict(
        list_repo=MagicMock(),
        item_repo=MagicMock(),
        subject=MagicMock(),
    )


@pytest.fixture
def svc(deps):
    return ShoppingListService(**deps)


# ── create_list ─────────────────────────────────────────────────────────────

def test_create_list_adds_to_repo(svc, deps):
    svc.create_list(id="l1", name="Weekly", owner_id="u1")
    deps["list_repo"].add.assert_called_once()
    added = deps["list_repo"].add.call_args[0][0]
    assert added.id == "l1"
    assert added.status == ListStatus.ACTIVE


def test_create_list_returns_shopping_list(svc):
    result = svc.create_list(id="l1", name="Weekly", owner_id="u1")
    assert isinstance(result, ShoppingList)


def test_create_list_sets_created_at_to_now(svc):
    before = datetime.now()
    result = svc.create_list(id="l1", name="Weekly", owner_id="u1")
    after = datetime.now()
    assert before <= result.created_at <= after


# ── archive_list ─────────────────────────────────────────────────────────────

def test_archive_list_updates_status(svc, deps):
    deps["list_repo"].get_by_id.return_value = _make_list()
    svc.archive_list("l1")
    updated = deps["list_repo"].update.call_args[0][0]
    assert updated.status == ListStatus.ARCHIVED


def test_archive_list_not_found_raises(svc, deps):
    deps["list_repo"].get_by_id.return_value = None
    with pytest.raises(KeyError):
        svc.archive_list("ghost")


def test_archive_already_archived_raises(svc, deps):
    deps["list_repo"].get_by_id.return_value = _make_list(status=ListStatus.ARCHIVED)
    with pytest.raises(ValueError):
        svc.archive_list("l1")


# ── get_lists_by_owner ───────────────────────────────────────────────────────

def test_get_lists_by_owner_delegates_to_repo(svc, deps):
    deps["list_repo"].find_by_owner.return_value = [_make_list()]
    result = svc.get_lists_by_owner("u1")
    deps["list_repo"].find_by_owner.assert_called_once_with("u1")
    assert len(result) == 1


def test_get_lists_by_owner_empty_returns_empty(svc, deps):
    deps["list_repo"].find_by_owner.return_value = []
    assert svc.get_lists_by_owner("u99") == []


# ── add_item ─────────────────────────────────────────────────────────────────

def test_add_item_adds_to_item_repo(svc, deps):
    deps["list_repo"].get_by_id.return_value = _make_list()
    deps["item_repo"].find_by_list.return_value = []
    svc.add_item(list_id="l1", item_id="i1", name="Milk", quantity=2.0)
    deps["item_repo"].add.assert_called_once()
    added = deps["item_repo"].add.call_args[0][0]
    assert added.name == "Milk"
    assert added.quantity == 2.0


def test_add_item_list_not_found_raises(svc, deps):
    deps["list_repo"].get_by_id.return_value = None
    with pytest.raises(KeyError):
        svc.add_item(list_id="ghost", item_id="i1", name="Milk", quantity=1.0)


def test_add_item_to_archived_list_raises(svc, deps):
    deps["list_repo"].get_by_id.return_value = _make_list(status=ListStatus.ARCHIVED)
    with pytest.raises(ValueError):
        svc.add_item(list_id="l1", item_id="i1", name="Milk", quantity=1.0)


def test_add_item_fires_item_added_event(svc, deps):
    deps["list_repo"].get_by_id.return_value = _make_list()
    deps["item_repo"].find_by_list.return_value = []
    svc.add_item(list_id="l1", item_id="i1", name="Milk", quantity=1.0)
    deps["subject"].notify.assert_called_once()
    event = deps["subject"].notify.call_args[0][0]
    assert event.type == EventType.ITEM_ADDED
    assert event.list_id == "l1"


def test_add_item_returns_shopping_item(svc, deps):
    deps["list_repo"].get_by_id.return_value = _make_list()
    deps["item_repo"].find_by_list.return_value = []
    result = svc.add_item(list_id="l1", item_id="i1", name="Milk", quantity=1.0)
    assert isinstance(result, ShoppingItem)


# ── remove_item ───────────────────────────────────────────────────────────────

def test_remove_item_deletes_from_repo(svc, deps):
    deps["item_repo"].get_by_id.return_value = _make_item()
    deps["item_repo"].find_by_list.return_value = []
    svc.remove_item("i1")
    deps["item_repo"].delete.assert_called_once_with("i1")


def test_remove_item_not_found_raises(svc, deps):
    deps["item_repo"].get_by_id.return_value = None
    with pytest.raises(KeyError):
        svc.remove_item("ghost")


def test_remove_item_fires_item_removed_event(svc, deps):
    deps["item_repo"].get_by_id.return_value = _make_item()
    deps["item_repo"].find_by_list.return_value = []
    svc.remove_item("i1")
    event = deps["subject"].notify.call_args[0][0]
    assert event.type == EventType.ITEM_REMOVED


def test_remove_last_item_fires_list_completed_when_all_purchased(svc, deps):
    item = _make_item(is_purchased=True)
    deps["item_repo"].get_by_id.return_value = item
    deps["item_repo"].find_by_list.return_value = []
    svc.remove_item("i1")
    calls = [c[0][0].type for c in deps["subject"].notify.call_args_list]
    assert EventType.ITEM_REMOVED in calls


def test_add_item_completes_list_when_all_purchased_after_add(svc, deps):
    deps["list_repo"].get_by_id.return_value = _make_list()
    existing = _make_item(id="i0", is_purchased=True)
    new_item = _make_item(id="i1", is_purchased=False)
    deps["item_repo"].find_by_list.return_value = [existing]
    svc.add_item(list_id="l1", item_id="i1", name="Milk", quantity=1.0)
    # not completed because new item is not purchased; just ITEM_ADDED fired
    calls = [c[0][0].type for c in deps["subject"].notify.call_args_list]
    assert EventType.ITEM_ADDED in calls
