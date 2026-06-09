import pytest
from datetime import datetime
from models.shopping_item import ShoppingItem


def _make_item(**kwargs):
    defaults = dict(
        id="i1", list_id="l1", name="Milk", quantity=2.0,
        unit="L", category="Dairy", price=1.50,
        added_at=datetime(2025, 1, 1),
    )
    defaults.update(kwargs)
    return ShoppingItem(**defaults)


def test_shopping_item_creates_with_valid_fields():
    item = _make_item()
    assert item.id == "i1"
    assert item.list_id == "l1"
    assert item.name == "Milk"
    assert item.quantity == 2.0
    assert item.unit == "L"
    assert item.category == "Dairy"
    assert item.price == 1.50
    assert item.is_purchased is False
    assert item.purchased_at is None


def test_shopping_item_is_purchased_defaults_false():
    item = _make_item()
    assert item.is_purchased is False


def test_shopping_item_added_at_defaults_to_now_when_omitted():
    before = datetime.now()
    item = ShoppingItem(id="i1", list_id="l1", name="Eggs", quantity=12.0)
    after = datetime.now()
    assert before <= item.added_at <= after


def test_shopping_item_unit_defaults_empty():
    item = ShoppingItem(id="i1", list_id="l1", name="Eggs", quantity=12.0)
    assert item.unit == ""


def test_shopping_item_category_defaults_empty():
    item = ShoppingItem(id="i1", list_id="l1", name="Eggs", quantity=12.0)
    assert item.category == ""


def test_shopping_item_price_defaults_zero():
    item = ShoppingItem(id="i1", list_id="l1", name="Eggs", quantity=12.0)
    assert item.price == 0.0


def test_shopping_item_empty_id_raises():
    with pytest.raises(ValueError, match="id"):
        _make_item(id="")


def test_shopping_item_whitespace_id_raises():
    with pytest.raises(ValueError, match="id"):
        _make_item(id="  ")


def test_shopping_item_empty_list_id_raises():
    with pytest.raises(ValueError, match="list_id"):
        _make_item(list_id="")


def test_shopping_item_whitespace_list_id_raises():
    with pytest.raises(ValueError, match="list_id"):
        _make_item(list_id="  ")


def test_shopping_item_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        _make_item(name="")


def test_shopping_item_whitespace_name_raises():
    with pytest.raises(ValueError, match="name"):
        _make_item(name="  ")


def test_shopping_item_zero_quantity_raises():
    with pytest.raises(ValueError, match="quantity"):
        _make_item(quantity=0.0)


def test_shopping_item_negative_quantity_raises():
    with pytest.raises(ValueError, match="quantity"):
        _make_item(quantity=-1.0)


def test_shopping_item_negative_price_raises():
    with pytest.raises(ValueError, match="price"):
        _make_item(price=-0.01)


def test_shopping_item_zero_price_is_valid():
    item = _make_item(price=0.0)
    assert item.price == 0.0


def test_shopping_item_with_purchased_at():
    ts = datetime(2025, 1, 2)
    item = _make_item(is_purchased=True, purchased_at=ts)
    assert item.is_purchased is True
    assert item.purchased_at == ts


def test_shopping_item_equality_by_fields():
    i1 = _make_item()
    i2 = _make_item()
    assert i1 == i2


def test_shopping_item_inequality_different_id():
    i1 = _make_item(id="i1")
    i2 = _make_item(id="i2")
    assert i1 != i2
