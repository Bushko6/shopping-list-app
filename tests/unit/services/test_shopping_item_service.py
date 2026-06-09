import pytest
from datetime import datetime
from unittest.mock import MagicMock
from models.shopping_item import ShoppingItem
from models.enums import SortOrder
from services.shopping_item_service import ShoppingItemService
from services.sort_strategies import AlphabeticalSortStrategy


def _make_item(id="i1", list_id="l1", name="Milk", is_purchased=False, price=1.0):
    return ShoppingItem(id=id, list_id=list_id, name=name, quantity=1.0,
                        price=price, is_purchased=is_purchased,
                        added_at=datetime(2025, 1, 1))


@pytest.fixture
def deps():
    return dict(
        item_repo=MagicMock(),
        sort_strategy=AlphabeticalSortStrategy(),
    )


@pytest.fixture
def svc(deps):
    return ShoppingItemService(**deps)


# ── mark_purchased ────────────────────────────────────────────────────────────

def test_mark_purchased_sets_flag(svc, deps):
    deps["item_repo"].get_by_id.return_value = _make_item(is_purchased=False)
    result = svc.mark_purchased("i1")
    assert result.is_purchased is True


def test_mark_purchased_sets_purchased_at(svc, deps):
    deps["item_repo"].get_by_id.return_value = _make_item(is_purchased=False)
    before = datetime.now()
    result = svc.mark_purchased("i1")
    after = datetime.now()
    assert before <= result.purchased_at <= after


def test_mark_purchased_saves_to_repo(svc, deps):
    deps["item_repo"].get_by_id.return_value = _make_item()
    svc.mark_purchased("i1")
    deps["item_repo"].update.assert_called_once()


def test_mark_purchased_not_found_raises(svc, deps):
    deps["item_repo"].get_by_id.return_value = None
    with pytest.raises(KeyError):
        svc.mark_purchased("ghost")


def test_mark_purchased_already_purchased_raises(svc, deps):
    deps["item_repo"].get_by_id.return_value = _make_item(is_purchased=True)
    with pytest.raises(ValueError):
        svc.mark_purchased("i1")


# ── unmark_purchased ──────────────────────────────────────────────────────────

def test_unmark_purchased_clears_flag(svc, deps):
    deps["item_repo"].get_by_id.return_value = _make_item(is_purchased=True)
    result = svc.unmark_purchased("i1")
    assert result.is_purchased is False


def test_unmark_purchased_clears_purchased_at(svc, deps):
    item = _make_item(is_purchased=True)
    item.purchased_at = datetime(2025, 1, 2)
    deps["item_repo"].get_by_id.return_value = item
    result = svc.unmark_purchased("i1")
    assert result.purchased_at is None


def test_unmark_purchased_saves_to_repo(svc, deps):
    deps["item_repo"].get_by_id.return_value = _make_item(is_purchased=True)
    svc.unmark_purchased("i1")
    deps["item_repo"].update.assert_called_once()


def test_unmark_purchased_not_found_raises(svc, deps):
    deps["item_repo"].get_by_id.return_value = None
    with pytest.raises(KeyError):
        svc.unmark_purchased("ghost")


def test_unmark_purchased_not_purchased_raises(svc, deps):
    deps["item_repo"].get_by_id.return_value = _make_item(is_purchased=False)
    with pytest.raises(ValueError):
        svc.unmark_purchased("i1")


# ── bulk_mark_purchased ───────────────────────────────────────────────────────

def test_bulk_mark_purchased_marks_all_unpurchased_in_list(svc, deps):
    deps["item_repo"].find_by_list.return_value = [
        _make_item(id="i1", is_purchased=False),
        _make_item(id="i2", is_purchased=False),
    ]
    deps["item_repo"].get_by_id.side_effect = lambda id: _make_item(id=id)
    results = svc.bulk_mark_purchased("l1")
    assert len(results) == 2
    assert all(i.is_purchased for i in results)


def test_bulk_mark_purchased_skips_already_purchased(svc, deps):
    deps["item_repo"].find_by_list.return_value = [
        _make_item(id="i1", is_purchased=True),
        _make_item(id="i2", is_purchased=False),
    ]
    deps["item_repo"].get_by_id.side_effect = lambda id: (
        _make_item(id=id, is_purchased=(id == "i1"))
    )
    results = svc.bulk_mark_purchased("l1")
    assert len(results) == 1
    assert results[0].id == "i2"


def test_bulk_mark_purchased_empty_list_returns_empty(svc, deps):
    deps["item_repo"].find_by_list.return_value = []
    assert svc.bulk_mark_purchased("l1") == []


# ── get_items_sorted ──────────────────────────────────────────────────────────

def test_get_items_sorted_uses_injected_strategy(svc, deps):
    items = [_make_item(id="i1", name="Zucchini"),
             _make_item(id="i2", name="Apple")]
    deps["item_repo"].find_by_list.return_value = items
    result = svc.get_items_sorted("l1")
    assert result[0].name == "Apple"


def test_get_items_sorted_empty_list_returns_empty(svc, deps):
    deps["item_repo"].find_by_list.return_value = []
    assert svc.get_items_sorted("l1") == []


# ── get_unpurchased ────────────────────────────────────────────────────────────

def test_get_unpurchased_delegates_to_repo(svc, deps):
    deps["item_repo"].find_unpurchased_by_list.return_value = [_make_item()]
    result = svc.get_unpurchased("l1")
    deps["item_repo"].find_unpurchased_by_list.assert_called_once_with("l1")
    assert len(result) == 1


def test_get_unpurchased_empty_returns_empty(svc, deps):
    deps["item_repo"].find_unpurchased_by_list.return_value = []
    assert svc.get_unpurchased("l1") == []


# ── _check_completion (subject wired) ─────────────────────────────────────────

def _make_svc_with_subject():
    from unittest.mock import MagicMock
    from services.observer import ShoppingListSubject, EventType
    item_repo = MagicMock()
    subject = MagicMock(spec=ShoppingListSubject)
    svc = ShoppingItemService(item_repo=item_repo,
                              sort_strategy=AlphabeticalSortStrategy(),
                              subject=subject)
    return svc, item_repo, subject


def test_mark_purchased_fires_list_completed_when_all_purchased():
    from services.observer import EventType
    svc, item_repo, subject = _make_svc_with_subject()
    item_repo.get_by_id.return_value = _make_item(id="i1", is_purchased=False)
    item_repo.find_by_list.return_value = [_make_item(id="i1", is_purchased=True)]
    svc.mark_purchased("i1")
    event = subject.notify.call_args[0][0]
    assert event.type == EventType.LIST_COMPLETED
    assert event.list_id == "l1"


def test_mark_purchased_no_completion_when_another_item_unpurchased():
    from services.observer import EventType
    svc, item_repo, subject = _make_svc_with_subject()
    item_repo.get_by_id.return_value = _make_item(id="i1", is_purchased=False)
    item_repo.find_by_list.return_value = [
        _make_item(id="i1", is_purchased=True),
        _make_item(id="i2", is_purchased=False),
    ]
    svc.mark_purchased("i1")
    subject.notify.assert_not_called()


def test_mark_purchased_no_subject_does_not_raise():
    item_repo = MagicMock()
    svc = ShoppingItemService(item_repo=item_repo,
                              sort_strategy=AlphabeticalSortStrategy())
    item_repo.get_by_id.return_value = _make_item(id="i1", is_purchased=False)
    item_repo.find_by_list.return_value = [_make_item(id="i1", is_purchased=True)]
    svc.mark_purchased("i1")  # must not raise


def test_bulk_mark_purchased_fires_list_completed():
    from services.observer import EventType
    svc, item_repo, subject = _make_svc_with_subject()
    item_repo.find_by_list.side_effect = [
        [_make_item(id="i1", is_purchased=False),
         _make_item(id="i2", is_purchased=False)],
        [_make_item(id="i1", is_purchased=True),
         _make_item(id="i2", is_purchased=True)],
    ]
    svc.bulk_mark_purchased("l1")
    event = subject.notify.call_args[0][0]
    assert event.type == EventType.LIST_COMPLETED


def test_bulk_mark_purchased_no_completion_when_none_newly_marked():
    svc, item_repo, subject = _make_svc_with_subject()
    item_repo.find_by_list.return_value = [
        _make_item(id="i1", is_purchased=True),
    ]
    svc.bulk_mark_purchased("l1")
    subject.notify.assert_not_called()


def test_bulk_mark_purchased_no_subject_does_not_raise():
    item_repo = MagicMock()
    svc = ShoppingItemService(item_repo=item_repo,
                              sort_strategy=AlphabeticalSortStrategy())
    item_repo.find_by_list.return_value = [_make_item(id="i1", is_purchased=False)]
    svc.bulk_mark_purchased("l1")  # must not raise
