import threading
import unittest

from costledger.ledger import Entry, Ledger


def entry(key: str, cost: int) -> Entry:
    return Entry(key, "small", input_tokens=10, output_tokens=5, cost_micros=cost)


class LedgerTest(unittest.TestCase):
    def test_totals_are_per_key(self):
        ledger = Ledger()
        ledger.record(entry("a", 100))
        ledger.record(entry("b", 30))
        ledger.record(entry("a", 7))
        self.assertEqual(ledger.total_micros("a"), 107)
        self.assertEqual(ledger.total_micros("b"), 30)
        self.assertEqual(ledger.total_micros(), 137)
        self.assertEqual(ledger.total_tokens("a"), 30)

    def test_unknown_key_totals_zero(self):
        self.assertEqual(Ledger().total_micros("nobody"), 0)

    def test_concurrent_records_are_not_lost(self):
        ledger = Ledger()
        threads = [
            threading.Thread(target=lambda: [ledger.record(entry("a", 1)) for _ in range(200)])
            for _ in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(ledger.entries("a")), 1600)


if __name__ == "__main__":
    unittest.main()
