import pytest
from datetime import datetime
from unittest.mock import MagicMock
from models.shopping_list import ShoppingList
from models.shopping_item import ShoppingItem
from models.enums import ListStatus
from services.persistence_service import PersistenceService


def _make_list(id="l1"):
    return ShoppingList(id=id, name="Shop", owner_id="u1",
                        created_at=datetime(2025, 1, 1), status=ListStatus.ACTIVE)


def _make_item(id="i1", list_id="l1"):
    return ShoppingItem(id=id, list_id=list_id, name="Milk", quantity=1.0,
                        added_at=datetime(2025, 1, 1))


@pytest.fixture
def deps():
    return dict(
        list_repo=MagicMock(),
        item_repo=MagicMock(),
    )


@pytest.fixture
def svc(deps):
    return PersistenceService(**deps)


# ── save_list ─────────────────────────────────────────────────────────────────

def test_save_list_new_calls_add(svc, deps):
    deps["list_repo"].get_by_id.return_value = None
    sl = _make_list()
    svc.save_list(sl)
    deps["list_repo"].add.assert_called_once_with(sl)


def test_save_list_existing_calls_update(svc, deps):
    sl = _make_list()
    deps["list_repo"].get_by_id.return_value = sl
    svc.save_list(sl)
    deps["list_repo"].update.assert_called_once_with(sl)


def test_save_list_returns_the_list(svc, deps):
    deps["list_repo"].get_by_id.return_value = None
    sl = _make_list()
    result = svc.save_list(sl)
    assert result == sl


# ── load_list ─────────────────────────────────────────────────────────────────

def test_load_list_returns_from_repo(svc, deps):
    sl = _make_list()
    deps["list_repo"].get_by_id.return_value = sl
    result = svc.load_list("l1")
    assert result == sl


def test_load_list_not_found_returns_none(svc, deps):
    deps["list_repo"].get_by_id.return_value = None
    assert svc.load_list("ghost") is None


def test_load_list_queries_correct_id(svc, deps):
    deps["list_repo"].get_by_id.return_value = None
    svc.load_list("l42")
    deps["list_repo"].get_by_id.assert_called_once_with("l42")


# ── save_item ─────────────────────────────────────────────────────────────────

def test_save_item_new_calls_add(svc, deps):
    deps["item_repo"].get_by_id.return_value = None
    item = _make_item()
    svc.save_item(item)
    deps["item_repo"].add.assert_called_once_with(item)


def test_save_item_existing_calls_update(svc, deps):
    item = _make_item()
    deps["item_repo"].get_by_id.return_value = item
    svc.save_item(item)
    deps["item_repo"].update.assert_called_once_with(item)


def test_save_item_returns_the_item(svc, deps):
    deps["item_repo"].get_by_id.return_value = None
    item = _make_item()
    result = svc.save_item(item)
    assert result == item


# ── load_item ─────────────────────────────────────────────────────────────────

def test_load_item_returns_from_repo(svc, deps):
    item = _make_item()
    deps["item_repo"].get_by_id.return_value = item
    assert svc.load_item("i1") == item


def test_load_item_not_found_returns_none(svc, deps):
    deps["item_repo"].get_by_id.return_value = None
    assert svc.load_item("ghost") is None
