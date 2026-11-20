"""Append-only record of completed calls, totalled per key."""

import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    key: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_micros: int


class Ledger:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: list[Entry] = []

    def record(self, entry: Entry) -> None:
        with self._lock:
            self._entries.append(entry)

    def entries(self, key: str | None = None) -> list[Entry]:
        with self._lock:
            return [e for e in self._entries if key is None or e.key == key]

    def total_micros(self, key: str | None = None) -> int:
        return sum(e.cost_micros for e in self.entries(key))

    def total_tokens(self, key: str | None = None) -> int:
        return sum(e.input_tokens + e.output_tokens for e in self.entries(key))
