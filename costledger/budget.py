"""Spend caps that reserve before a call and settle after it."""

import threading


class BudgetExceeded(Exception):
    pass


class Budgets:
    """Per-key caps in micro-USD.

    A call reserves its worst-case cost up front, so two concurrent callers
    cannot both pass a check that only one of them can afford. Settling
    replaces the reservation with the actual cost.
    """

    def __init__(self, limits: dict[str, int]) -> None:
        self._limits = dict(limits)
        self._committed: dict[str, int] = {}
        self._lock = threading.Lock()

    def reserve(self, key: str, amount: int) -> None:
        limit = self._limits.get(key)
        if limit is None:
            raise BudgetExceeded(f"no budget configured for key {key!r}")
        with self._lock:
            used = self._committed.get(key, 0)
            if used + amount > limit:
                raise BudgetExceeded(
                    f"key {key!r}: reserving {amount} on top of {used} exceeds limit {limit}"
                )
            self._committed[key] = used + amount

    def settle(self, key: str, reserved: int, actual: int) -> None:
        with self._lock:
            self._committed[key] = self._committed[key] - reserved + actual

    def release(self, key: str, reserved: int) -> None:
        self.settle(key, reserved, 0)

    def remaining(self, key: str) -> int:
        with self._lock:
            return self._limits[key] - self._committed.get(key, 0)
