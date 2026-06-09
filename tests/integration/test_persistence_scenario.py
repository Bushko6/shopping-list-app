"""
Integration: persistence scenarios using JsonFile repos.
Save, reload, verify data matches. File-not-found and corrupted-JSON errors.
"""
import json
import pytest
from datetime import datetime
from pathlib import Path

from storage.json_file.shopping_list_repo import JsonFileShoppingListRepository
from storage.json_file.shopping_item_repo import JsonFileShoppingItemRepository
from services.shopping_list_service import ShoppingListService
from services.shopping_item_service import ShoppingItemService
from services.persistence_service import PersistenceService
from services.sort_strategies import AlphabeticalSortStrategy
from services.observer import ShoppingListSubject, NotificationLog, ListCompletionObserver
from models.shopping_list import ShoppingList
from models.shopping_item import ShoppingItem
from models.enums import ListStatus


def _make_list_svc(list_repo, item_repo):
    subject = ShoppingListSubject()
    subject.subscribe(ListCompletionObserver(NotificationLog()))
    return ShoppingListService(list_repo, item_repo, subject)


# ── save then reload ──────────────────────────────────────────────────────────

def test_save_list_reload_name_matches(tmp_path):
    path = str(tmp_path / "lists.json")
    repo1 = JsonFileShoppingListRepository(path)
    svc = _make_list_svc(repo1, JsonFileShoppingItemRepository(str(tmp_path / "items.json")))
    svc.create_list("l1", "Weekly", "u1")

    repo2 = JsonFileShoppingListRepository(path)
    sl = repo2.get_by_id("l1")
    assert sl is not None
    assert sl.name == "Weekly"


def test_save_list_reload_owner_matches(tmp_path):
    path = str(tmp_path / "lists.json")
    repo1 = JsonFileShoppingListRepository(path)
    svc = _make_list_svc(repo1, JsonFileShoppingItemRepository(str(tmp_path / "items.json")))
    svc.create_list("l1", "Weekly", "u1")

    repo2 = JsonFileShoppingListRepository(path)
    assert repo2.get_by_id("l1").owner_id == "u1"


def test_save_multiple_lists_all_reload(tmp_path):
    path = str(tmp_path / "lists.json")
    repo1 = JsonFileShoppingListRepository(path)
    svc = _make_list_svc(repo1, JsonFileShoppingItemRepository(str(tmp_path / "items.json")))
    svc.create_list("l1", "Weekly", "u1")
    svc.create_list("l2", "Monthly", "u1")

    repo2 = JsonFileShoppingListRepository(path)
    assert repo2.get_by_id("l1") is not None
    assert repo2.get_by_id("l2") is not None


def test_archive_persists_across_reload(tmp_path):
    path = str(tmp_path / "lists.json")
    item_path = str(tmp_path / "items.json")
    repo1 = JsonFileShoppingListRepository(path)
    item_repo = JsonFileShoppingItemRepository(item_path)
    svc = _make_list_svc(repo1, item_repo)
    svc.create_list("l1", "Weekly", "u1")
    svc.archive_list("l1")

    repo2 = JsonFileShoppingListRepository(path)
    assert repo2.get_by_id("l1").status == ListStatus.ARCHIVED


def test_save_item_reload_name_matches(tmp_path):
    path = str(tmp_path / "items.json")
    repo1 = JsonFileShoppingItemRepository(path)
    item = ShoppingItem(id="i1", list_id="l1", name="Milk", quantity=2.0,
                        added_at=datetime(2025, 1, 1))
    repo1.add(item)

    repo2 = JsonFileShoppingItemRepository(path)
    assert repo2.get_by_id("i1").name == "Milk"


def test_save_item_reload_quantity_matches(tmp_path):
    path = str(tmp_path / "items.json")
    repo1 = JsonFileShoppingItemRepository(path)
    item = ShoppingItem(id="i1", list_id="l1", name="Milk", quantity=3.5,
                        added_at=datetime(2025, 1, 1))
    repo1.add(item)

    repo2 = JsonFileShoppingItemRepository(path)
    assert repo2.get_by_id("i1").quantity == 3.5


def test_save_item_purchased_state_persists(tmp_path):
    path = str(tmp_path / "items.json")
    repo = JsonFileShoppingItemRepository(path)
    item = ShoppingItem(id="i1", list_id="l1", name="Milk", quantity=1.0,
                        is_purchased=True, added_at=datetime(2025, 1, 1))
    repo.add(item)

    repo2 = JsonFileShoppingItemRepository(path)
    assert repo2.get_by_id("i1").is_purchased is True


def test_save_item_category_persists(tmp_path):
    path = str(tmp_path / "items.json")
    repo = JsonFileShoppingItemRepository(path)
    item = ShoppingItem(id="i1", list_id="l1", name="Milk", quantity=1.0,
                        category="Dairy", added_at=datetime(2025, 1, 1))
    repo.add(item)

    repo2 = JsonFileShoppingItemRepository(path)
    assert repo2.get_by_id("i1").category == "Dairy"


def test_save_item_price_persists(tmp_path):
    path = str(tmp_path / "items.json")
    repo = JsonFileShoppingItemRepository(path)
    item = ShoppingItem(id="i1", list_id="l1", name="Milk", quantity=1.0,
                        price=1.99, added_at=datetime(2025, 1, 1))
    repo.add(item)

    repo2 = JsonFileShoppingItemRepository(path)
    assert repo2.get_by_id("i1").price == 1.99


def test_purchased_at_timestamp_survives_round_trip(tmp_path):
    path = str(tmp_path / "items.json")
    ts = datetime(2025, 6, 1, 12, 30)
    repo = JsonFileShoppingItemRepository(path)
    item = ShoppingItem(id="i1", list_id="l1", name="Milk", quantity=1.0,
                        is_purchased=True, purchased_at=ts,
                        added_at=datetime(2025, 1, 1))
    repo.add(item)

    repo2 = JsonFileShoppingItemRepository(path)
    assert repo2.get_by_id("i1").purchased_at == ts


def test_null_purchased_at_survives_round_trip(tmp_path):
    path = str(tmp_path / "items.json")
    repo = JsonFileShoppingItemRepository(path)
    item = ShoppingItem(id="i1", list_id="l1", name="Milk", quantity=1.0,
                        added_at=datetime(2025, 1, 1))
    repo.add(item)

    repo2 = JsonFileShoppingItemRepository(path)
    assert repo2.get_by_id("i1").purchased_at is None


# ── persistence_service ───────────────────────────────────────────────────────

def test_persistence_service_save_new_then_load(tmp_path):
    path_l = str(tmp_path / "lists.json")
    path_i = str(tmp_path / "items.json")
    list_repo = JsonFileShoppingListRepository(path_l)
    item_repo = JsonFileShoppingItemRepository(path_i)
    svc = PersistenceService(list_repo, item_repo)

    sl = ShoppingList(id="l1", name="Weekly", owner_id="u1",
                      created_at=datetime(2025, 1, 1), status=ListStatus.ACTIVE)
    svc.save_list(sl)
    loaded = svc.load_list("l1")
    assert loaded is not None
    assert loaded.name == "Weekly"


def test_persistence_service_save_update_then_load(tmp_path):
    path_l = str(tmp_path / "lists.json")
    path_i = str(tmp_path / "items.json")
    list_repo = JsonFileShoppingListRepository(path_l)
    item_repo = JsonFileShoppingItemRepository(path_i)
    svc = PersistenceService(list_repo, item_repo)

    sl = ShoppingList(id="l1", name="Weekly", owner_id="u1",
                      created_at=datetime(2025, 1, 1), status=ListStatus.ACTIVE)
    svc.save_list(sl)
    sl.status = ListStatus.ARCHIVED
    svc.save_list(sl)
    loaded = svc.load_list("l1")
    assert loaded.status == ListStatus.ARCHIVED


def test_persistence_service_load_not_found_returns_none(tmp_path):
    path_l = str(tmp_path / "lists.json")
    path_i = str(tmp_path / "items.json")
    svc = PersistenceService(
        JsonFileShoppingListRepository(path_l),
        JsonFileShoppingItemRepository(path_i),
    )
    assert svc.load_list("nonexistent") is None


def test_persistence_service_save_item_then_reload(tmp_path):
    path_l = str(tmp_path / "lists.json")
    path_i = str(tmp_path / "items.json")
    list_repo = JsonFileShoppingListRepository(path_l)
    item_repo = JsonFileShoppingItemRepository(path_i)
    svc = PersistenceService(list_repo, item_repo)

    item = ShoppingItem(id="i1", list_id="l1", name="Eggs", quantity=12.0,
                        added_at=datetime(2025, 1, 1))
    svc.save_item(item)
    loaded = svc.load_item("i1")
    assert loaded is not None
    assert loaded.quantity == 12.0


def test_persistence_service_item_not_found_returns_none(tmp_path):
    svc = PersistenceService(
        JsonFileShoppingListRepository(str(tmp_path / "l.json")),
        JsonFileShoppingItemRepository(str(tmp_path / "i.json")),
    )
    assert svc.load_item("ghost") is None


# ── file-not-found (new repo on missing file is fine) ────────────────────────

def test_new_repo_missing_file_starts_empty(tmp_path):
    path = str(tmp_path / "never_created.json")
    repo = JsonFileShoppingListRepository(path)
    assert repo.list_all() == []


def test_new_item_repo_missing_file_starts_empty(tmp_path):
    path = str(tmp_path / "never_created.json")
    repo = JsonFileShoppingItemRepository(path)
    assert repo.list_all() == []


# ── corrupted JSON ────────────────────────────────────────────────────────────

def test_corrupted_json_file_raises_on_load(tmp_path):
    path = tmp_path / "lists.json"
    path.write_text("{ this is not valid json [[[")
    with pytest.raises(Exception):
        JsonFileShoppingListRepository(str(path))


def test_corrupted_item_json_raises_on_load(tmp_path):
    path = tmp_path / "items.json"
    path.write_text("definitely not json")
    with pytest.raises(Exception):
        JsonFileShoppingItemRepository(str(path))


# ── full save-reload scenario ─────────────────────────────────────────────────

def test_full_save_create_new_service_load_data_matches(tmp_path):
    list_path = str(tmp_path / "lists.json")
    item_path = str(tmp_path / "items.json")

    # First session: create data
    list_repo1 = JsonFileShoppingListRepository(list_path)
    item_repo1 = JsonFileShoppingItemRepository(item_path)
    svc1 = _make_list_svc(list_repo1, item_repo1)
    svc1.create_list("l1", "Weekly", "u1")
    svc1.add_item("l1", "i1", "Milk", 2.0, price=1.99)
    svc1.add_item("l1", "i2", "Bread", 1.0, price=2.50)

    # Second session: reload
    list_repo2 = JsonFileShoppingListRepository(list_path)
    item_repo2 = JsonFileShoppingItemRepository(item_path)
    item_svc2 = ShoppingItemService(item_repo2, AlphabeticalSortStrategy())

    items = item_svc2.get_items_sorted("l1")
    assert len(items) == 2
    names = {i.name for i in items}
    assert names == {"Milk", "Bread"}
