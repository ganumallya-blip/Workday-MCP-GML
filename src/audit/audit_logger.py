"""Audit logger abstraction and memory-backed implementation."""
from abc import ABC, abstractmethod
from .models import AuditEvent

class AuditLogger(ABC):
    @abstractmethod
    async def log(self, event: AuditEvent) -> None: ...
    @abstractmethod
    async def list_events(self, limit: int = 100) -> list[AuditEvent]: ...

class InMemoryAuditLogger(AuditLogger):
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    async def log(self, event: AuditEvent) -> None:
        self._events.append(event)

    async def list_events(self, limit: int = 100) -> list[AuditEvent]:
        return list(reversed(self._events[-limit:]))
