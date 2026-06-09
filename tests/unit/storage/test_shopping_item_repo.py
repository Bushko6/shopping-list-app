import pytest
from datetime import datetime
from models.shopping_item import ShoppingItem
from storage.memory.shopping_item_repo import InMemoryShoppingItemRepository


def _make_item(id="i1", list_id="l1", name="Milk", quantity=2.0,
               is_purchased=False, price=1.5):
    return ShoppingItem(id=id, list_id=list_id, name=name, quantity=quantity,
                        price=price, is_purchased=is_purchased,
                        added_at=datetime(2025, 1, 1))


@pytest.fixture
def repo():
    return InMemoryShoppingItemRepository()


def test_add_and_get_by_id(repo):
    item = _make_item()
    repo.add(item)
    assert repo.get_by_id("i1") == item


def test_get_by_id_missing_returns_none(repo):
    assert repo.get_by_id("x") is None


def test_add_duplicate_raises(repo):
    repo.add(_make_item())
    with pytest.raises(ValueError):
        repo.add(_make_item())


def test_list_all_empty(repo):
    assert repo.list_all() == []


def test_list_all_returns_all(repo):
    repo.add(_make_item(id="i1"))
    repo.add(_make_item(id="i2"))
    assert len(repo.list_all()) == 2


def test_update_replaces_existing(repo):
    repo.add(_make_item())
    updated = _make_item(is_purchased=True)
    repo.update(updated)
    assert repo.get_by_id("i1").is_purchased is True


def test_update_missing_raises(repo):
    with pytest.raises(KeyError):
        repo.update(_make_item())


def test_delete_removes_entry(repo):
    repo.add(_make_item())
    repo.delete("i1")
    assert repo.get_by_id("i1") is None


def test_delete_missing_raises(repo):
    with pytest.raises(KeyError):
        repo.delete("ghost")


def test_list_all_reflects_delete(repo):
    repo.add(_make_item(id="i1"))
    repo.add(_make_item(id="i2"))
    repo.delete("i1")
    assert len(repo.list_all()) == 1


def test_find_by_list_returns_matching(repo):
    repo.add(_make_item(id="i1", list_id="l1"))
    repo.add(_make_item(id="i2", list_id="l2"))
    repo.add(_make_item(id="i3", list_id="l1"))
    result = repo.find_by_list("l1")
    assert len(result) == 2
    assert all(i.list_id == "l1" for i in result)


def test_find_by_list_no_match_returns_empty(repo):
    assert repo.find_by_list("l99") == []


def test_find_unpurchased_by_list_filters_correctly(repo):
    repo.add(_make_item(id="i1", list_id="l1", is_purchased=False))
    repo.add(_make_item(id="i2", list_id="l1", is_purchased=True))
    repo.add(_make_item(id="i3", list_id="l1", is_purchased=False))
    result = repo.find_unpurchased_by_list("l1")
    assert len(result) == 2
    assert all(not i.is_purchased for i in result)


def test_find_unpurchased_by_list_all_purchased_returns_empty(repo):
    repo.add(_make_item(id="i1", list_id="l1", is_purchased=True))
    assert repo.find_unpurchased_by_list("l1") == []
