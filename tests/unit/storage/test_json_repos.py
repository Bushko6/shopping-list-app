import json
import pytest
from datetime import datetime
from pathlib import Path
from models.shopping_list import ShoppingList
from models.shopping_item import ShoppingItem
from models.enums import ListStatus
from storage.json_file.shopping_list_repo import JsonFileShoppingListRepository
from storage.json_file.shopping_item_repo import JsonFileShoppingItemRepository


def _make_list(id="l1", name="Shop", owner_id="u1", status=ListStatus.ACTIVE):
    return ShoppingList(id=id, name=name, owner_id=owner_id,
                        created_at=datetime(2025, 1, 1), status=status)


def _make_item(id="i1", list_id="l1", name="Milk", quantity=2.0,
               is_purchased=False, price=1.5):
    return ShoppingItem(id=id, list_id=list_id, name=name, quantity=quantity,
                        price=price, is_purchased=is_purchased,
                        added_at=datetime(2025, 1, 1))


# ── ShoppingList JSON repo ──────────────────────────────────────────────────

@pytest.fixture
def list_repo(tmp_path):
    return JsonFileShoppingListRepository(str(tmp_path / "lists.json"))


def test_json_list_add_and_get_by_id(list_repo):
    sl = _make_list()
    list_repo.add(sl)
    assert list_repo.get_by_id("l1").name == "Shop"


def test_json_list_persists_across_instances(tmp_path):
    path = str(tmp_path / "lists.json")
    repo1 = JsonFileShoppingListRepository(path)
    repo1.add(_make_list())

    repo2 = JsonFileShoppingListRepository(path)
    assert repo2.get_by_id("l1") is not None


def test_json_list_add_duplicate_raises(list_repo):
    list_repo.add(_make_list())
    with pytest.raises(ValueError):
        list_repo.add(_make_list())


def test_json_list_update_persists(tmp_path):
    path = str(tmp_path / "lists.json")
    repo = JsonFileShoppingListRepository(path)
    repo.add(_make_list())
    repo.update(_make_list(status=ListStatus.ARCHIVED))

    reloaded = JsonFileShoppingListRepository(path)
    assert reloaded.get_by_id("l1").status == ListStatus.ARCHIVED


def test_json_list_delete_persists(tmp_path):
    path = str(tmp_path / "lists.json")
    repo = JsonFileShoppingListRepository(path)
    repo.add(_make_list())
    repo.delete("l1")

    reloaded = JsonFileShoppingListRepository(path)
    assert reloaded.get_by_id("l1") is None


def test_json_list_update_missing_raises(list_repo):
    with pytest.raises(KeyError):
        list_repo.update(_make_list())


def test_json_list_delete_missing_raises(list_repo):
    with pytest.raises(KeyError):
        list_repo.delete("ghost")


def test_json_list_find_by_owner(list_repo):
    list_repo.add(_make_list(id="l1", owner_id="u1"))
    list_repo.add(_make_list(id="l2", owner_id="u2"))
    assert len(list_repo.find_by_owner("u1")) == 1


def test_json_list_empty_file_created_on_first_add(tmp_path):
    path = tmp_path / "lists.json"
    repo = JsonFileShoppingListRepository(str(path))
    repo.add(_make_list())
    assert path.exists()
    data = json.loads(path.read_text())
    assert len(data) == 1


def test_json_list_list_all_returns_all(list_repo):
    list_repo.add(_make_list(id="l1"))
    list_repo.add(_make_list(id="l2"))
    assert len(list_repo.list_all()) == 2


def test_json_list_loads_from_existing_file(tmp_path):
    path = tmp_path / "lists.json"
    path.write_text(json.dumps([{
        "id": "l1", "name": "Shop", "owner_id": "u1",
        "created_at": "2025-01-01T00:00:00", "status": "ACTIVE",
    }]))
    repo = JsonFileShoppingListRepository(str(path))
    assert repo.get_by_id("l1") is not None


# ── ShoppingItem JSON repo ──────────────────────────────────────────────────

@pytest.fixture
def item_repo(tmp_path):
    return JsonFileShoppingItemRepository(str(tmp_path / "items.json"))


def test_json_item_add_and_get_by_id(item_repo):
    item_repo.add(_make_item())
    assert item_repo.get_by_id("i1").name == "Milk"


def test_json_item_persists_across_instances(tmp_path):
    path = str(tmp_path / "items.json")
    repo1 = JsonFileShoppingItemRepository(path)
    repo1.add(_make_item())

    repo2 = JsonFileShoppingItemRepository(path)
    assert repo2.get_by_id("i1") is not None


def test_json_item_add_duplicate_raises(item_repo):
    item_repo.add(_make_item())
    with pytest.raises(ValueError):
        item_repo.add(_make_item())


def test_json_item_update_persists(tmp_path):
    path = str(tmp_path / "items.json")
    repo = JsonFileShoppingItemRepository(path)
    repo.add(_make_item())
    repo.update(_make_item(is_purchased=True))

    reloaded = JsonFileShoppingItemRepository(path)
    assert reloaded.get_by_id("i1").is_purchased is True


def test_json_item_delete_persists(tmp_path):
    path = str(tmp_path / "items.json")
    repo = JsonFileShoppingItemRepository(path)
    repo.add(_make_item())
    repo.delete("i1")

    reloaded = JsonFileShoppingItemRepository(path)
    assert reloaded.get_by_id("i1") is None


def test_json_item_update_missing_raises(item_repo):
    with pytest.raises(KeyError):
        item_repo.update(_make_item())


def test_json_item_delete_missing_raises(item_repo):
    with pytest.raises(KeyError):
        item_repo.delete("ghost")


def test_json_item_find_by_list(item_repo):
    item_repo.add(_make_item(id="i1", list_id="l1"))
    item_repo.add(_make_item(id="i2", list_id="l2"))
    assert len(item_repo.find_by_list("l1")) == 1


def test_json_item_find_unpurchased_by_list(item_repo):
    item_repo.add(_make_item(id="i1", list_id="l1", is_purchased=False))
    item_repo.add(_make_item(id="i2", list_id="l1", is_purchased=True))
    result = item_repo.find_unpurchased_by_list("l1")
    assert len(result) == 1


def test_json_item_list_all_returns_all(item_repo):
    item_repo.add(_make_item(id="i1"))
    item_repo.add(_make_item(id="i2"))
    assert len(item_repo.list_all()) == 2


def test_json_item_purchased_at_survives_round_trip(tmp_path):
    path = str(tmp_path / "items.json")
    repo = JsonFileShoppingItemRepository(path)
    ts = datetime(2025, 3, 15, 10, 30)
    item = ShoppingItem(id="i1", list_id="l1", name="Eggs", quantity=12.0,
                        is_purchased=True, purchased_at=ts,
                        added_at=datetime(2025, 1, 1))
    repo.add(item)
    reloaded = JsonFileShoppingItemRepository(path)
    assert reloaded.get_by_id("i1").purchased_at == ts
