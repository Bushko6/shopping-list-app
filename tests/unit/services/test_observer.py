import pytest
from unittest.mock import MagicMock
from services.observer import (
    ShoppingListSubject,
    ListCompletionObserver,
    NotificationLog,
    ItemEvent,
    EventType,
)


def _make_subject():
    return ShoppingListSubject()


# ── subscribe / unsubscribe ─────────────────────────────────────────────────

def test_subscribe_and_receive_event():
    subject = _make_subject()
    observer = MagicMock()
    subject.subscribe(observer)
    event = ItemEvent(type=EventType.ITEM_ADDED, list_id="l1", item_id="i1")
    subject.notify(event)
    observer.on_event.assert_called_once_with(event)


def test_subscribe_is_idempotent():
    subject = _make_subject()
    observer = MagicMock()
    subject.subscribe(observer)
    subject.subscribe(observer)
    event = ItemEvent(type=EventType.ITEM_ADDED, list_id="l1", item_id="i1")
    subject.notify(event)
    observer.on_event.assert_called_once()


def test_unsubscribe_stops_notifications():
    subject = _make_subject()
    observer = MagicMock()
    subject.subscribe(observer)
    subject.unsubscribe(observer)
    subject.notify(ItemEvent(type=EventType.ITEM_ADDED, list_id="l1", item_id="i1"))
    observer.on_event.assert_not_called()


def test_unsubscribe_unknown_observer_raises():
    subject = _make_subject()
    observer = MagicMock()
    with pytest.raises(ValueError):
        subject.unsubscribe(observer)


def test_notify_dispatches_to_snapshot_safe_on_unsubscribe_mid_dispatch():
    subject = _make_subject()
    event = ItemEvent(type=EventType.ITEM_ADDED, list_id="l1", item_id="i1")

    class SelfRemovingObserver:
        def on_event(self, ev):
            subject.unsubscribe(self)

    obs = SelfRemovingObserver()
    subject.subscribe(obs)
    subject.notify(event)  # must not raise


def test_notify_multiple_observers():
    subject = _make_subject()
    obs1, obs2 = MagicMock(), MagicMock()
    subject.subscribe(obs1)
    subject.subscribe(obs2)
    event = ItemEvent(type=EventType.LIST_COMPLETED, list_id="l1", item_id=None)
    subject.notify(event)
    obs1.on_event.assert_called_once()
    obs2.on_event.assert_called_once()


# ── EventType values ────────────────────────────────────────────────────────

def test_event_types_exist():
    assert EventType.ITEM_ADDED is not None
    assert EventType.ITEM_REMOVED is not None
    assert EventType.LIST_COMPLETED is not None


# ── ListCompletionObserver ──────────────────────────────────────────────────

def test_list_completion_observer_records_on_completed_event():
    log = NotificationLog()
    obs = ListCompletionObserver(log)
    event = ItemEvent(type=EventType.LIST_COMPLETED, list_id="l1", item_id=None)
    obs.on_event(event)
    notes = log.get_notifications("l1")
    assert len(notes) == 1
    assert "l1" in notes[0]


def test_list_completion_observer_ignores_non_completed_events():
    log = NotificationLog()
    obs = ListCompletionObserver(log)
    obs.on_event(ItemEvent(type=EventType.ITEM_ADDED, list_id="l1", item_id="i1"))
    obs.on_event(ItemEvent(type=EventType.ITEM_REMOVED, list_id="l1", item_id="i1"))
    assert log.get_notifications("l1") == []


# ── NotificationLog ─────────────────────────────────────────────────────────

def test_notification_log_get_unknown_list_returns_empty():
    log = NotificationLog()
    assert log.get_notifications("unknown") == []


def test_notification_log_stores_multiple_notifications():
    log = NotificationLog()
    log.add("l1", "First message")
    log.add("l1", "Second message")
    notes = log.get_notifications("l1")
    assert len(notes) == 2


def test_notification_log_different_lists_isolated():
    log = NotificationLog()
    log.add("l1", "msg for l1")
    log.add("l2", "msg for l2")
    assert len(log.get_notifications("l1")) == 1
    assert len(log.get_notifications("l2")) == 1
