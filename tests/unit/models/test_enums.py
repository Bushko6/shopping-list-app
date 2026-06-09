from models.enums import ListStatus, SortOrder


def test_list_status_has_active():
    assert ListStatus.ACTIVE is not None


def test_list_status_has_archived():
    assert ListStatus.ARCHIVED is not None


def test_list_status_active_and_archived_are_distinct():
    assert ListStatus.ACTIVE != ListStatus.ARCHIVED


def test_sort_order_has_all_five_values():
    names = {s.name for s in SortOrder}
    assert names == {"ALPHABETICAL", "CATEGORY", "PRICE_ASC", "PRICE_DESC", "UNPURCHASED_FIRST"}


def test_sort_order_values_are_strings():
    for order in SortOrder:
        assert isinstance(order.value, str)
