from typing import Optional
from storage.interfaces import UserRepository
from models.user import User


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._store: dict[str, User] = {}

    def add(self, user: User) -> None:
        if user.id in self._store:
            raise ValueError(f"User '{user.id}' already exists")
        self._store[user.id] = user

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self._store.get(user_id)

    def list_all(self) -> list[User]:
        return list(self._store.values())

    def update(self, user: User) -> None:
        if user.id not in self._store:
            raise KeyError(f"User '{user.id}' not found")
        self._store[user.id] = user

    def delete(self, user_id: str) -> None:
        if user_id not in self._store:
            raise KeyError(f"User '{user_id}' not found")
        del self._store[user_id]

    def find_by_email(self, email: str) -> Optional[User]:
        for user in self._store.values():
            if user.email == email:
                return user
        return None
