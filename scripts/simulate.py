"""Hammer one budget from many threads and check it is never overspent.

Uses the fake provider and an illustrative price table, so the output says
nothing about real provider pricing.
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from costledger.budget import BudgetExceeded, Budgets
from costledger.gateway import BudgetedGateway
from costledger.ledger import Ledger
from costledger.pricing import Price, PriceTable
from costledger.provider import FakeProvider, Request

KEY = "team-a"
MODEL = "small"
LIMIT_MICROS = 50_000
THREADS = 16
CALLS_PER_THREAD = 50
PRICES = PriceTable({MODEL: Price(input_per_mtok=500_000, output_per_mtok=1_500_000)})


def main() -> int:
    ledger = Ledger()
    budgets = Budgets({KEY: LIMIT_MICROS})
    provider = FakeProvider(reply_tokens=60)
    gateway = BudgetedGateway(provider, PRICES, budgets, ledger)
    refused = []

    def worker() -> None:
        for i in range(CALLS_PER_THREAD):
            try:
                gateway.complete(KEY, Request(MODEL, f"summarise ticket {i} " * 20, max_tokens=200))
            except BudgetExceeded:
                refused.append(1)

    threads = [threading.Thread(target=worker) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    spent = ledger.total_micros(KEY)
    attempts = THREADS * CALLS_PER_THREAD
    print(f"attempts={attempts} served={len(ledger.entries(KEY))} refused={len(refused)}")
    print(f"limit={LIMIT_MICROS} spent={spent} remaining={budgets.remaining(KEY)}")
    checks = {
        "spend within limit": spent <= LIMIT_MICROS,
        "ledger matches budget": budgets.remaining(KEY) == LIMIT_MICROS - spent,
        "every served call hit the provider once": provider.calls == len(ledger.entries(KEY)),
        "served + refused == attempts": len(ledger.entries(KEY)) + len(refused) == attempts,
        "some calls were refused": len(refused) > 0,
    }
    for name, ok in checks.items():
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
