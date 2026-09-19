from typing import Any
from typing_extensions import Self


class LogRecorder:
    """Record logger calls made at the background-provider boundary."""

    def __init__(self) -> None:
        self.debug_messages: list[str] = []
        self.warning_messages: list[str] = []
        self.error_messages: list[str] = []
        self.exception_messages: list[str] = []

    def debug(self, message: str) -> None:
        self.debug_messages.append(message)

    def warning(self, message: str) -> None:
        self.warning_messages.append(message)

    def error(self, message: str) -> None:
        self.error_messages.append(message)

    def exception(self, message: str) -> None:
        self.exception_messages.append(message)

    def opt(self, **_: Any) -> Self:
        return self
