import pytest
from datetime import datetime
from models.shopping_list import ShoppingList
from models.enums import ListStatus
from storage.memory.shopping_list_repo import InMemoryShoppingListRepository


def _make_list(id="l1", name="Weekly", owner_id="u1", status=ListStatus.ACTIVE):
    return ShoppingList(id=id, name=name, owner_id=owner_id,
                        created_at=datetime(2025, 1, 1), status=status)


@pytest.fixture
def repo():
    return InMemoryShoppingListRepository()


def test_add_and_get_by_id(repo):
    sl = _make_list()
    repo.add(sl)
    assert repo.get_by_id("l1") == sl


def test_get_by_id_missing_returns_none(repo):
    assert repo.get_by_id("missing") is None


def test_add_duplicate_raises(repo):
    repo.add(_make_list())
    with pytest.raises(ValueError):
        repo.add(_make_list())


def test_list_all_empty(repo):
    assert repo.list_all() == []


def test_list_all_returns_all(repo):
    repo.add(_make_list(id="l1"))
    repo.add(_make_list(id="l2"))
    assert len(repo.list_all()) == 2


def test_update_replaces_existing(repo):
    sl = _make_list()
    repo.add(sl)
    updated = _make_list(status=ListStatus.ARCHIVED)
    repo.update(updated)
    assert repo.get_by_id("l1").status == ListStatus.ARCHIVED


def test_update_missing_raises(repo):
    with pytest.raises(KeyError):
        repo.update(_make_list())


def test_delete_removes_entry(repo):
    repo.add(_make_list())
    repo.delete("l1")
    assert repo.get_by_id("l1") is None


def test_delete_missing_raises(repo):
    with pytest.raises(KeyError):
        repo.delete("ghost")


def test_list_all_reflects_delete(repo):
    repo.add(_make_list(id="l1"))
    repo.add(_make_list(id="l2"))
    repo.delete("l1")
    assert len(repo.list_all()) == 1


def test_find_by_owner_returns_matching(repo):
    repo.add(_make_list(id="l1", owner_id="u1"))
    repo.add(_make_list(id="l2", owner_id="u2"))
    repo.add(_make_list(id="l3", owner_id="u1"))
    result = repo.find_by_owner("u1")
    assert len(result) == 2
    assert all(sl.owner_id == "u1" for sl in result)


def test_find_by_owner_no_match_returns_empty(repo):
    repo.add(_make_list(id="l1", owner_id="u1"))
    assert repo.find_by_owner("u99") == []
