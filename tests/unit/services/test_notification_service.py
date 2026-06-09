import pytest
from unittest.mock import MagicMock
from services.notification_service import NotificationService
from services.observer import NotificationLog


@pytest.fixture
def log():
    return NotificationLog()


@pytest.fixture
def svc(log):
    return NotificationService(notification_log=log)


def test_get_notifications_returns_empty_for_unknown_list(svc):
    assert svc.get_notifications("unknown") == []


def test_get_notifications_returns_stored_messages(svc, log):
    log.add("l1", "List complete!")
    log.add("l1", "Another message")
    result = svc.get_notifications("l1")
    assert len(result) == 2


def test_get_notifications_different_lists_isolated(svc, log):
    log.add("l1", "msg1")
    log.add("l2", "msg2")
    assert len(svc.get_notifications("l1")) == 1
    assert len(svc.get_notifications("l2")) == 1


def test_get_notifications_returns_correct_messages(svc, log):
    log.add("l1", "Done!")
    messages = svc.get_notifications("l1")
    assert messages[0] == "Done!"


def test_get_all_notifications_returns_all_lists(svc, log):
    log.add("l1", "msg1")
    log.add("l2", "msg2")
    log.add("l3", "msg3")
    result = svc.get_all_notifications()
    assert len(result) == 3


def test_get_all_notifications_empty_returns_empty_dict(svc):
    assert svc.get_all_notifications() == {}
