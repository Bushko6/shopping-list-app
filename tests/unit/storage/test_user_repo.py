import pytest
from models.user import User
from storage.memory.user_repo import InMemoryUserRepository


def _user(id="u1", username="alice", email="alice@example.com", is_active=True):
    return User(id=id, username=username, email=email, is_active=is_active)


@pytest.fixture
def repo():
    return InMemoryUserRepository()


def test_add_and_get_by_id(repo):
    u = _user()
    repo.add(u)
    assert repo.get_by_id("u1") == u


def test_get_by_id_missing_returns_none(repo):
    assert repo.get_by_id("x") is None


def test_add_duplicate_raises(repo):
    repo.add(_user())
    with pytest.raises(ValueError):
        repo.add(_user())


def test_list_all_empty(repo):
    assert repo.list_all() == []


def test_list_all_returns_all(repo):
    repo.add(_user(id="u1", email="a@a.com"))
    repo.add(_user(id="u2", email="b@b.com"))
    assert len(repo.list_all()) == 2


def test_update_replaces_existing(repo):
    repo.add(_user())
    repo.update(_user(is_active=False))
    assert repo.get_by_id("u1").is_active is False


def test_update_missing_raises(repo):
    with pytest.raises(KeyError):
        repo.update(_user())


def test_delete_removes_entry(repo):
    repo.add(_user())
    repo.delete("u1")
    assert repo.get_by_id("u1") is None


def test_delete_missing_raises(repo):
    with pytest.raises(KeyError):
        repo.delete("ghost")


def test_find_by_email_returns_match(repo):
    repo.add(_user(id="u1", email="alice@example.com"))
    assert repo.find_by_email("alice@example.com").id == "u1"


def test_find_by_email_no_match_returns_none(repo):
    assert repo.find_by_email("nobody@example.com") is None


def test_find_by_email_items_exist_but_no_match_returns_none(repo):
    repo.add(_user(id="u1", email="alice@example.com"))
    assert repo.find_by_email("nobody@example.com") is None
