from services.observer import NotificationLog


class NotificationService:
    def __init__(self, notification_log: NotificationLog) -> None:
        self._log = notification_log

    def get_notifications(self, list_id: str) -> list[str]:
        return self._log.get_notifications(list_id)

    def get_all_notifications(self) -> dict[str, list[str]]:
        return self._log.get_all()
