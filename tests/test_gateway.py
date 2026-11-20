import unittest

from costledger.budget import BudgetExceeded, Budgets
from costledger.gateway import BudgetedGateway
from costledger.ledger import Ledger
from costledger.pricing import Price, PriceTable
from costledger.provider import FakeProvider, Request

PRICES = PriceTable({"small": Price(input_per_mtok=1_000_000, output_per_mtok=2_000_000)})


class BrokenProvider:
    def complete(self, request):
        raise TimeoutError("upstream timed out")


def build(limit, provider=None):
    ledger = Ledger()
    budgets = Budgets({"team": limit})
    gateway = BudgetedGateway(provider or FakeProvider(reply_tokens=10), PRICES, budgets, ledger)
    return gateway, budgets, ledger


class BudgetedGatewayTest(unittest.TestCase):
    def test_actual_cost_is_recorded_and_unused_reservation_returned(self):
        gateway, budgets, ledger = build(limit=10_000)
        # prompt 40 chars = 10 tokens in; fake replies 10 tokens out
        gateway.complete("team", Request("small", "p" * 40, max_tokens=100))
        self.assertEqual(ledger.total_micros("team"), 10 * 1 + 10 * 2)
        self.assertEqual(budgets.remaining("team"), 10_000 - 30)

    def test_call_that_cannot_fit_worst_case_never_reaches_the_provider(self):
        provider = FakeProvider()
        gateway, _, ledger = build(limit=50, provider=provider)
        with self.assertRaises(BudgetExceeded):
            gateway.complete("team", Request("small", "p" * 40, max_tokens=100))
        self.assertEqual(provider.calls, 0)
        self.assertEqual(ledger.entries(), [])

    def test_provider_failure_releases_the_reservation(self):
        gateway, budgets, ledger = build(limit=10_000, provider=BrokenProvider())
        with self.assertRaises(TimeoutError):
            gateway.complete("team", Request("small", "hello", max_tokens=100))
        self.assertEqual(budgets.remaining("team"), 10_000)
        self.assertEqual(ledger.entries(), [])

    def test_budget_is_spent_down_across_calls(self):
        gateway, _, ledger = build(limit=300)
        request = Request("small", "p" * 40, max_tokens=100)  # worst case 210
        for _ in range(4):  # each settles at 30, so 4 calls leave 120 used
            gateway.complete("team", request)
        self.assertEqual(ledger.total_micros("team"), 4 * 30)
        with self.assertRaises(BudgetExceeded):
            gateway.complete("team", request)  # 120 + 210 > 300


if __name__ == "__main__":
    unittest.main()
