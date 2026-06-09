from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EventType(Enum):
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"
    LIST_COMPLETED = "list_completed"


@dataclass
class ItemEvent:
    type: EventType
    list_id: str
    item_id: Optional[str]


class ItemObserver(ABC):
    @abstractmethod
    def on_event(self, event: ItemEvent) -> None: ...


class ShoppingListSubject:
    def __init__(self) -> None:
        self._observers: list[ItemObserver] = []

    def subscribe(self, observer: ItemObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: ItemObserver) -> None:
        if observer not in self._observers:
            raise ValueError("Observer not subscribed")
        self._observers.remove(observer)

    def notify(self, event: ItemEvent) -> None:
        for observer in list(self._observers):
            observer.on_event(event)


class NotificationLog:
    def __init__(self) -> None:
        self._store: dict[str, list[str]] = {}

    def add(self, list_id: str, message: str) -> None:
        self._store.setdefault(list_id, []).append(message)

    def get_notifications(self, list_id: str) -> list[str]:
        return self._store.get(list_id, [])

    def get_all(self) -> dict[str, list[str]]:
        return dict(self._store)


class ListCompletionObserver(ItemObserver):
    def __init__(self, log: NotificationLog) -> None:
        self._log = log

    def on_event(self, event: ItemEvent) -> None:
        if event.type == EventType.LIST_COMPLETED:
            self._log.add(event.list_id, f"List '{event.list_id}' is complete!")
