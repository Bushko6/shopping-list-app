import pytest
from datetime import datetime
from models.shopping_item import ShoppingItem
from services.sort_strategies import (
    AlphabeticalSortStrategy,
    CategorySortStrategy,
    PriceAscSortStrategy,
    PriceDescSortStrategy,
    UnpurchasedFirstStrategy,
    SortStrategyFactory,
)


def _item(id="i1", name="Milk", category="Dairy", price=1.0, is_purchased=False):
    return ShoppingItem(id=id, list_id="l1", name=name, quantity=1.0,
                        category=category, price=price,
                        is_purchased=is_purchased,
                        added_at=datetime(2025, 1, 1))


# ── AlphabeticalSortStrategy ────────────────────────────────────────────────

def test_alphabetical_empty_list():
    assert AlphabeticalSortStrategy().sort([]) == []


def test_alphabetical_single_item():
    items = [_item(name="Milk")]
    assert AlphabeticalSortStrategy().sort(items) == items


def test_alphabetical_sorts_ascending():
    items = [_item(id="i1", name="Zucchini"), _item(id="i2", name="Apple"),
             _item(id="i3", name="Milk")]
    result = AlphabeticalSortStrategy().sort(items)
    assert [i.name for i in result] == ["Apple", "Milk", "Zucchini"]


def test_alphabetical_does_not_mutate_original():
    items = [_item(id="i1", name="Z"), _item(id="i2", name="A")]
    original_order = [i.id for i in items]
    AlphabeticalSortStrategy().sort(items)
    assert [i.id for i in items] == original_order


# ── CategorySortStrategy ────────────────────────────────────────────────────

def test_category_empty_list():
    assert CategorySortStrategy().sort([]) == []


def test_category_groups_by_category_then_name():
    items = [
        _item(id="i1", name="Milk",   category="Dairy"),
        _item(id="i2", name="Beef",   category="Meat"),
        _item(id="i3", name="Cheese", category="Dairy"),
    ]
    result = CategorySortStrategy().sort(items)
    categories = [i.category for i in result]
    assert categories == ["Dairy", "Dairy", "Meat"]
    assert result[0].name == "Cheese"
    assert result[1].name == "Milk"


def test_category_items_without_category_sorted_last():
    items = [
        _item(id="i1", name="Apple", category=""),
        _item(id="i2", name="Milk",  category="Dairy"),
    ]
    result = CategorySortStrategy().sort(items)
    assert result[0].category == "Dairy"
    assert result[-1].category == ""


# ── PriceAscSortStrategy ────────────────────────────────────────────────────

def test_price_asc_empty_list():
    assert PriceAscSortStrategy().sort([]) == []


def test_price_asc_sorts_ascending():
    items = [_item(id="i1", price=3.0), _item(id="i2", price=1.0),
             _item(id="i3", price=2.0)]
    result = PriceAscSortStrategy().sort(items)
    assert [i.price for i in result] == [1.0, 2.0, 3.0]


def test_price_asc_ties_broken_by_name():
    items = [_item(id="i1", name="Zucchini", price=1.0),
             _item(id="i2", name="Apple",    price=1.0)]
    result = PriceAscSortStrategy().sort(items)
    assert result[0].name == "Apple"


# ── PriceDescSortStrategy ───────────────────────────────────────────────────

def test_price_desc_empty_list():
    assert PriceDescSortStrategy().sort([]) == []


def test_price_desc_sorts_descending():
    items = [_item(id="i1", price=1.0), _item(id="i2", price=3.0),
             _item(id="i3", price=2.0)]
    result = PriceDescSortStrategy().sort(items)
    assert [i.price for i in result] == [3.0, 2.0, 1.0]


def test_price_desc_ties_broken_by_name():
    items = [_item(id="i1", name="Zucchini", price=2.0),
             _item(id="i2", name="Apple",    price=2.0)]
    result = PriceDescSortStrategy().sort(items)
    assert result[0].name == "Apple"


# ── UnpurchasedFirstStrategy ────────────────────────────────────────────────

def test_unpurchased_first_empty_list():
    assert UnpurchasedFirstStrategy().sort([]) == []


def test_unpurchased_first_puts_unpurchased_before_purchased():
    items = [
        _item(id="i1", name="Milk",  is_purchased=True),
        _item(id="i2", name="Bread", is_purchased=False),
        _item(id="i3", name="Eggs",  is_purchased=False),
    ]
    result = UnpurchasedFirstStrategy().sort(items)
    assert not result[0].is_purchased
    assert not result[1].is_purchased
    assert result[2].is_purchased


def test_unpurchased_first_within_group_sorted_alphabetically():
    items = [
        _item(id="i1", name="Zucchini", is_purchased=False),
        _item(id="i2", name="Apple",    is_purchased=False),
    ]
    result = UnpurchasedFirstStrategy().sort(items)
    assert result[0].name == "Apple"


def test_unpurchased_first_all_purchased_still_sorts():
    items = [_item(id="i1", name="Z", is_purchased=True),
             _item(id="i2", name="A", is_purchased=True)]
    result = UnpurchasedFirstStrategy().sort(items)
    assert result[0].name == "A"


# ── SortStrategyFactory ─────────────────────────────────────────────────────

def test_factory_returns_alphabetical():
    assert isinstance(SortStrategyFactory.from_name("alphabetical"),
                       AlphabeticalSortStrategy)


def test_factory_returns_category():
    assert isinstance(SortStrategyFactory.from_name("category"),
                       CategorySortStrategy)


def test_factory_returns_price_asc():
    assert isinstance(SortStrategyFactory.from_name("price_asc"),
                       PriceAscSortStrategy)


def test_factory_returns_price_desc():
    assert isinstance(SortStrategyFactory.from_name("price_desc"),
                       PriceDescSortStrategy)


def test_factory_returns_unpurchased_first():
    assert isinstance(SortStrategyFactory.from_name("unpurchased_first"),
                       UnpurchasedFirstStrategy)


def test_factory_unknown_name_raises():
    with pytest.raises(ValueError, match="Unknown sort strategy"):
        SortStrategyFactory.from_name("bogus")
