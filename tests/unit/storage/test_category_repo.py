import pytest
from models.category import Category
from storage.memory.category_repo import InMemoryCategoryRepository


def _cat(id="c1", name="Dairy", color="#fff"):
    return Category(id=id, name=name, color=color)


@pytest.fixture
def repo():
    return InMemoryCategoryRepository()


def test_add_and_get_by_id(repo):
    cat = _cat()
    repo.add(cat)
    assert repo.get_by_id("c1") == cat


def test_get_by_id_missing_returns_none(repo):
    assert repo.get_by_id("x") is None


def test_add_duplicate_raises(repo):
    repo.add(_cat())
    with pytest.raises(ValueError):
        repo.add(_cat())


def test_list_all_empty(repo):
    assert repo.list_all() == []


def test_list_all_returns_all(repo):
    repo.add(_cat(id="c1"))
    repo.add(_cat(id="c2"))
    assert len(repo.list_all()) == 2


def test_update_replaces_existing(repo):
    repo.add(_cat())
    repo.update(_cat(color="#000"))
    assert repo.get_by_id("c1").color == "#000"


def test_update_missing_raises(repo):
    with pytest.raises(KeyError):
        repo.update(_cat())


def test_delete_removes_entry(repo):
    repo.add(_cat())
    repo.delete("c1")
    assert repo.get_by_id("c1") is None


def test_delete_missing_raises(repo):
    with pytest.raises(KeyError):
        repo.delete("ghost")


def test_find_by_name_returns_match(repo):
    repo.add(_cat(id="c1", name="Dairy"))
    repo.add(_cat(id="c2", name="Meat"))
    assert repo.find_by_name("Dairy").id == "c1"


def test_find_by_name_no_match_returns_none(repo):
    assert repo.find_by_name("Nonexistent") is None


def test_find_by_name_items_exist_but_no_match_returns_none(repo):
    repo.add(_cat(id="c1", name="Dairy"))
    assert repo.find_by_name("Nonexistent") is None
