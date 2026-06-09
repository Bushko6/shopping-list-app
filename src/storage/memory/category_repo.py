from typing import Optional
from storage.interfaces import CategoryRepository
from models.category import Category


class InMemoryCategoryRepository(CategoryRepository):
    def __init__(self) -> None:
        self._store: dict[str, Category] = {}

    def add(self, category: Category) -> None:
        if category.id in self._store:
            raise ValueError(f"Category '{category.id}' already exists")
        self._store[category.id] = category

    def get_by_id(self, category_id: str) -> Optional[Category]:
        return self._store.get(category_id)

    def list_all(self) -> list[Category]:
        return list(self._store.values())

    def update(self, category: Category) -> None:
        if category.id not in self._store:
            raise KeyError(f"Category '{category.id}' not found")
        self._store[category.id] = category

    def delete(self, category_id: str) -> None:
        if category_id not in self._store:
            raise KeyError(f"Category '{category_id}' not found")
        del self._store[category_id]

    def find_by_name(self, name: str) -> Optional[Category]:
        for cat in self._store.values():
            if cat.name == name:
                return cat
        return None
