from abc import ABC, abstractmethod
from models.shopping_item import ShoppingItem


class SortStrategy(ABC):
    @abstractmethod
    def sort(self, items: list[ShoppingItem]) -> list[ShoppingItem]: ...


class AlphabeticalSortStrategy(SortStrategy):
    def sort(self, items: list[ShoppingItem]) -> list[ShoppingItem]:
        return sorted(items, key=lambda i: i.name.lower())


class CategorySortStrategy(SortStrategy):
    def sort(self, items: list[ShoppingItem]) -> list[ShoppingItem]:
        return sorted(items, key=lambda i: (i.category == "", i.category.lower(), i.name.lower()))


class PriceAscSortStrategy(SortStrategy):
    def sort(self, items: list[ShoppingItem]) -> list[ShoppingItem]:
        return sorted(items, key=lambda i: (i.price, i.name.lower()))


class PriceDescSortStrategy(SortStrategy):
    def sort(self, items: list[ShoppingItem]) -> list[ShoppingItem]:
        return sorted(items, key=lambda i: (-i.price, i.name.lower()))


class UnpurchasedFirstStrategy(SortStrategy):
    def sort(self, items: list[ShoppingItem]) -> list[ShoppingItem]:
        return sorted(items, key=lambda i: (i.is_purchased, i.name.lower()))


class SortStrategyFactory:
    _registry: dict[str, type[SortStrategy]] = {
        "alphabetical":     AlphabeticalSortStrategy,
        "category":         CategorySortStrategy,
        "price_asc":        PriceAscSortStrategy,
        "price_desc":       PriceDescSortStrategy,
        "unpurchased_first": UnpurchasedFirstStrategy,
    }

    @classmethod
    def from_name(cls, name: str) -> SortStrategy:
        klass = cls._registry.get(name)
        if klass is None:
            raise ValueError(f"Unknown sort strategy: '{name}'")
        return klass()
