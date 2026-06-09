import pytest
from datetime import datetime
from models.shopping_list import ShoppingList
from models.enums import ListStatus


def _make_list(**kwargs):
    defaults = dict(id="l1", name="Weekly Shop", owner_id="u1", created_at=datetime(2025, 1, 1))
    defaults.update(kwargs)
    return ShoppingList(**defaults)


def test_shopping_list_creates_with_valid_fields():
    sl = _make_list()
    assert sl.id == "l1"
    assert sl.name == "Weekly Shop"
    assert sl.owner_id == "u1"
    assert sl.status == ListStatus.ACTIVE


def test_shopping_list_status_defaults_active():
    sl = _make_list()
    assert sl.status == ListStatus.ACTIVE


def test_shopping_list_created_at_defaults_to_now_when_omitted():
    before = datetime.now()
    sl = ShoppingList(id="l1", name="Shop", owner_id="u1")
    after = datetime.now()
    assert before <= sl.created_at <= after


def test_shopping_list_empty_id_raises():
    with pytest.raises(ValueError, match="id"):
        _make_list(id="")


def test_shopping_list_whitespace_id_raises():
    with pytest.raises(ValueError, match="id"):
        _make_list(id="   ")


def test_shopping_list_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        _make_list(name="")


def test_shopping_list_whitespace_name_raises():
    with pytest.raises(ValueError, match="name"):
        _make_list(name="  ")


def test_shopping_list_empty_owner_id_raises():
    with pytest.raises(ValueError, match="owner_id"):
        _make_list(owner_id="")


def test_shopping_list_whitespace_owner_id_raises():
    with pytest.raises(ValueError, match="owner_id"):
        _make_list(owner_id="  ")


def test_is_archived_true_when_archived():
    sl = _make_list(status=ListStatus.ARCHIVED)
    assert sl.is_archived is True


def test_is_archived_false_when_active():
    sl = _make_list(status=ListStatus.ACTIVE)
    assert sl.is_archived is False


def test_is_active_true_when_active():
    sl = _make_list(status=ListStatus.ACTIVE)
    assert sl.is_active is True


def test_is_active_false_when_archived():
    sl = _make_list(status=ListStatus.ARCHIVED)
    assert sl.is_active is False


def test_shopping_list_equality_by_fields():
    sl1 = _make_list()
    sl2 = _make_list()
    assert sl1 == sl2


def test_shopping_list_inequality_different_id():
    sl1 = _make_list(id="l1")
    sl2 = _make_list(id="l2")
    assert sl1 != sl2
