import pytest
from models.user import User


def test_user_creates_with_valid_fields():
    u = User(id="u1", username="alice", email="alice@example.com")
    assert u.id == "u1"
    assert u.username == "alice"
    assert u.email == "alice@example.com"
    assert u.is_active is True


def test_user_is_active_defaults_true():
    u = User(id="u1", username="bob", email="bob@example.com")
    assert u.is_active is True


def test_user_can_be_created_inactive():
    u = User(id="u1", username="bob", email="bob@example.com", is_active=False)
    assert u.is_active is False


def test_user_empty_id_raises():
    with pytest.raises(ValueError, match="id"):
        User(id="", username="alice", email="alice@example.com")


def test_user_whitespace_id_raises():
    with pytest.raises(ValueError, match="id"):
        User(id="  ", username="alice", email="alice@example.com")


def test_user_empty_username_raises():
    with pytest.raises(ValueError, match="username"):
        User(id="u1", username="", email="alice@example.com")


def test_user_whitespace_username_raises():
    with pytest.raises(ValueError, match="username"):
        User(id="u1", username="  ", email="alice@example.com")


def test_user_email_without_at_raises():
    with pytest.raises(ValueError, match="email"):
        User(id="u1", username="alice", email="aliceexample.com")


def test_user_empty_email_raises():
    with pytest.raises(ValueError, match="email"):
        User(id="u1", username="alice", email="")


def test_user_equality_by_fields():
    u1 = User(id="u1", username="alice", email="alice@example.com")
    u2 = User(id="u1", username="alice", email="alice@example.com")
    assert u1 == u2


def test_user_inequality_different_id():
    u1 = User(id="u1", username="alice", email="alice@example.com")
    u2 = User(id="u2", username="alice", email="alice@example.com")
    assert u1 != u2
