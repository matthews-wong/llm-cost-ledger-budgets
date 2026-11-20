import threading
import unittest

from costledger.budget import BudgetExceeded, Budgets


class BudgetsTest(unittest.TestCase):
    def test_reserve_up_to_the_limit_then_refuse(self):
        budgets = Budgets({"a": 100})
        budgets.reserve("a", 60)
        budgets.reserve("a", 40)
        with self.assertRaises(BudgetExceeded) as ctx:
            budgets.reserve("a", 1)
        self.assertIn("'a'", str(ctx.exception))

    def test_settle_returns_the_unused_part(self):
        budgets = Budgets({"a": 100})
        budgets.reserve("a", 80)
        budgets.settle("a", reserved=80, actual=30)
        self.assertEqual(budgets.remaining("a"), 70)

    def test_release_frees_the_whole_reservation(self):
        budgets = Budgets({"a": 100})
        budgets.reserve("a", 80)
        budgets.release("a", 80)
        self.assertEqual(budgets.remaining("a"), 100)

    def test_unconfigured_key_is_refused(self):
        with self.assertRaises(BudgetExceeded) as ctx:
            Budgets({}).reserve("ghost", 1)
        self.assertIn("ghost", str(ctx.exception))

    def test_concurrent_reservations_never_overshoot(self):
        budgets = Budgets({"a": 50})
        granted = []

        def worker():
            try:
                budgets.reserve("a", 1)
                granted.append(1)
            except BudgetExceeded:
                pass

        threads = [threading.Thread(target=worker) for _ in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(granted), 50)
        self.assertEqual(budgets.remaining("a"), 0)


if __name__ == "__main__":
    unittest.main()
