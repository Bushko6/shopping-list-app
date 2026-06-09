from enum import Enum


class ListStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class SortOrder(Enum):
    ALPHABETICAL = "alphabetical"
    CATEGORY = "category"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    UNPURCHASED_FIRST = "unpurchased_first"
