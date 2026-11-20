import unittest

from costledger.pricing import Price, PriceTable, UnknownModelError
from costledger.provider import Usage

TABLE = PriceTable({"small": Price(input_per_mtok=500_000, output_per_mtok=1_500_000)})


class PriceTableTest(unittest.TestCase):
    def test_cost_is_input_plus_output(self):
        self.assertEqual(TABLE.cost("small", Usage(1_000, 1_000)), 2_000)

    def test_fractional_micro_usd_rounds_up(self):
        # 1 input token = 0.5 micro-USD -> 1
        self.assertEqual(TABLE.cost("small", Usage(1, 0)), 1)

    def test_zero_usage_is_free(self):
        self.assertEqual(TABLE.cost("small", Usage(0, 0)), 0)

    def test_unknown_model_names_the_model(self):
        with self.assertRaises(UnknownModelError) as ctx:
            TABLE.cost("mystery", Usage(1, 1))
        self.assertIn("mystery", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
