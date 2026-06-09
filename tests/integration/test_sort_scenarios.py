"""
Integration: sort strategy scenarios with real in-memory repos.
"""
import pytest
from storage.memory.shopping_list_repo import InMemoryShoppingListRepository
from storage.memory.shopping_item_repo import InMemoryShoppingItemRepository
from services.shopping_list_service import ShoppingListService
from services.shopping_item_service import ShoppingItemService
from services.sort_strategies import (
    AlphabeticalSortStrategy,
    CategorySortStrategy,
    PriceAscSortStrategy,
    PriceDescSortStrategy,
    UnpurchasedFirstStrategy,
    SortStrategyFactory,
)
from services.observer import ShoppingListSubject, NotificationLog, ListCompletionObserver


def _setup(strategy):
    list_repo = InMemoryShoppingListRepository()
    item_repo = InMemoryShoppingItemRepository()
    subject = ShoppingListSubject()
    subject.subscribe(ListCompletionObserver(NotificationLog()))
    list_svc = ShoppingListService(list_repo, item_repo, subject)
    item_svc = ShoppingItemService(item_repo, strategy)
    list_svc.create_list("l1", "Test List", "u1")
    return list_svc, item_svc


# ── Alphabetical ───────────────────────────────────────────────────────────────

def test_alphabetical_sort_empty_list():
    _, item_svc = _setup(AlphabeticalSortStrategy())
    assert item_svc.get_items_sorted("l1") == []


def test_alphabetical_sort_single_item():
    list_svc, item_svc = _setup(AlphabeticalSortStrategy())
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Milk"


def test_alphabetical_sort_multiple_items():
    list_svc, item_svc = _setup(AlphabeticalSortStrategy())
    list_svc.add_item("l1", "i1", "Zucchini", 1.0)
    list_svc.add_item("l1", "i2", "Apple", 1.0)
    list_svc.add_item("l1", "i3", "Mango", 1.0)
    result = item_svc.get_items_sorted("l1")
    assert [i.name for i in result] == ["Apple", "Mango", "Zucchini"]


def test_alphabetical_sort_case_insensitive():
    list_svc, item_svc = _setup(AlphabeticalSortStrategy())
    list_svc.add_item("l1", "i1", "banana", 1.0)
    list_svc.add_item("l1", "i2", "Apple", 1.0)
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Apple"


def test_alphabetical_sort_equal_names_stable():
    list_svc, item_svc = _setup(AlphabeticalSortStrategy())
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Milk", 2.0)
    result = item_svc.get_items_sorted("l1")
    assert len(result) == 2
    assert all(i.name == "Milk" for i in result)


# ── Category ───────────────────────────────────────────────────────────────────

def test_category_sort_empty_list():
    _, item_svc = _setup(CategorySortStrategy())
    assert item_svc.get_items_sorted("l1") == []


def test_category_sort_groups_same_category():
    list_svc, item_svc = _setup(CategorySortStrategy())
    list_svc.add_item("l1", "i1", "Beef", 1.0, category="Meat")
    list_svc.add_item("l1", "i2", "Milk", 1.0, category="Dairy")
    list_svc.add_item("l1", "i3", "Cheese", 1.0, category="Dairy")
    result = item_svc.get_items_sorted("l1")
    dairy = [i for i in result if i.category == "Dairy"]
    meat = [i for i in result if i.category == "Meat"]
    assert len(dairy) == 2
    assert len(meat) == 1
    assert result.index(dairy[0]) < result.index(meat[0])


def test_category_sort_no_category_goes_last():
    list_svc, item_svc = _setup(CategorySortStrategy())
    list_svc.add_item("l1", "i1", "Apple", 1.0, category="")
    list_svc.add_item("l1", "i2", "Milk", 1.0, category="Dairy")
    result = item_svc.get_items_sorted("l1")
    assert result[0].category == "Dairy"
    assert result[-1].category == ""


def test_category_sort_within_category_alphabetical():
    list_svc, item_svc = _setup(CategorySortStrategy())
    list_svc.add_item("l1", "i1", "Milk", 1.0, category="Dairy")
    list_svc.add_item("l1", "i2", "Cheese", 1.0, category="Dairy")
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Cheese"
    assert result[1].name == "Milk"


def test_category_sort_all_no_category():
    list_svc, item_svc = _setup(CategorySortStrategy())
    list_svc.add_item("l1", "i1", "Zucchini", 1.0, category="")
    list_svc.add_item("l1", "i2", "Apple", 1.0, category="")
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Apple"


# ── PriceAsc ───────────────────────────────────────────────────────────────────

def test_price_asc_sort_empty_list():
    _, item_svc = _setup(PriceAscSortStrategy())
    assert item_svc.get_items_sorted("l1") == []


def test_price_asc_sort_ascending_order():
    list_svc, item_svc = _setup(PriceAscSortStrategy())
    list_svc.add_item("l1", "i1", "Milk", 1.0, price=3.00)
    list_svc.add_item("l1", "i2", "Bread", 1.0, price=1.50)
    list_svc.add_item("l1", "i3", "Eggs", 1.0, price=2.00)
    result = item_svc.get_items_sorted("l1")
    assert [i.price for i in result] == [1.50, 2.00, 3.00]


def test_price_asc_sort_ties_broken_by_name():
    list_svc, item_svc = _setup(PriceAscSortStrategy())
    list_svc.add_item("l1", "i1", "Zucchini", 1.0, price=2.00)
    list_svc.add_item("l1", "i2", "Apple", 1.0, price=2.00)
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Apple"


def test_price_asc_sort_zero_price_first():
    list_svc, item_svc = _setup(PriceAscSortStrategy())
    list_svc.add_item("l1", "i1", "Milk", 1.0, price=1.00)
    list_svc.add_item("l1", "i2", "Water", 1.0, price=0.00)
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Water"


# ── PriceDesc ──────────────────────────────────────────────────────────────────

def test_price_desc_sort_empty_list():
    _, item_svc = _setup(PriceDescSortStrategy())
    assert item_svc.get_items_sorted("l1") == []


def test_price_desc_sort_descending_order():
    list_svc, item_svc = _setup(PriceDescSortStrategy())
    list_svc.add_item("l1", "i1", "Milk", 1.0, price=1.50)
    list_svc.add_item("l1", "i2", "Steak", 1.0, price=12.00)
    list_svc.add_item("l1", "i3", "Eggs", 1.0, price=3.00)
    result = item_svc.get_items_sorted("l1")
    assert [i.price for i in result] == [12.00, 3.00, 1.50]


def test_price_desc_sort_ties_broken_by_name():
    list_svc, item_svc = _setup(PriceDescSortStrategy())
    list_svc.add_item("l1", "i1", "Zucchini", 1.0, price=5.00)
    list_svc.add_item("l1", "i2", "Apple", 1.0, price=5.00)
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Apple"


# ── UnpurchasedFirst ──────────────────────────────────────────────────────────

def test_unpurchased_first_empty_list():
    _, item_svc = _setup(UnpurchasedFirstStrategy())
    assert item_svc.get_items_sorted("l1") == []


def test_unpurchased_first_puts_unpurchased_before_purchased():
    list_svc, item_svc = _setup(UnpurchasedFirstStrategy())
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    list_svc.add_item("l1", "i2", "Bread", 1.0)
    item_svc.mark_purchased("i1")
    result = item_svc.get_items_sorted("l1")
    assert result[0].is_purchased is False
    assert result[1].is_purchased is True


def test_unpurchased_first_all_purchased_alphabetical():
    list_svc, item_svc = _setup(UnpurchasedFirstStrategy())
    list_svc.add_item("l1", "i1", "Zucchini", 1.0)
    list_svc.add_item("l1", "i2", "Apple", 1.0)
    item_svc.mark_purchased("i1")
    item_svc.mark_purchased("i2")
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Apple"


def test_unpurchased_first_all_unpurchased_alphabetical():
    list_svc, item_svc = _setup(UnpurchasedFirstStrategy())
    list_svc.add_item("l1", "i1", "Zucchini", 1.0)
    list_svc.add_item("l1", "i2", "Apple", 1.0)
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Apple"


def test_unpurchased_first_single_purchased():
    list_svc, item_svc = _setup(UnpurchasedFirstStrategy())
    list_svc.add_item("l1", "i1", "Milk", 1.0)
    item_svc.mark_purchased("i1")
    result = item_svc.get_items_sorted("l1")
    assert result[0].is_purchased is True


# ── Factory ───────────────────────────────────────────────────────────────────

def test_factory_wired_alphabetical_sorts_real_items():
    strategy = SortStrategyFactory.from_name("alphabetical")
    list_svc, item_svc = _setup(strategy)
    list_svc.add_item("l1", "i1", "Zucchini", 1.0)
    list_svc.add_item("l1", "i2", "Apple", 1.0)
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Apple"


def test_factory_wired_price_asc_sorts_real_items():
    strategy = SortStrategyFactory.from_name("price_asc")
    list_svc, item_svc = _setup(strategy)
    list_svc.add_item("l1", "i1", "Steak", 1.0, price=10.00)
    list_svc.add_item("l1", "i2", "Rice", 1.0, price=2.00)
    result = item_svc.get_items_sorted("l1")
    assert result[0].name == "Rice"
