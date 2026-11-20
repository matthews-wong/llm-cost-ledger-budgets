"""Per-model prices in integer micro-USD so sums never drift like floats do."""

from dataclasses import dataclass

from .provider import Usage

TOKENS_PER_MTOK = 1_000_000


class UnknownModelError(KeyError):
    pass


@dataclass(frozen=True)
class Price:
    """Micro-USD per million tokens."""

    input_per_mtok: int
    output_per_mtok: int


def _ceil_div(numerator: int, denominator: int) -> int:
    return -(-numerator // denominator)


class PriceTable:
    def __init__(self, prices: dict[str, Price]) -> None:
        self._prices = dict(prices)

    def cost(self, model: str, usage: Usage) -> int:
        """Cost in micro-USD, rounded up so a ledger never under-reports."""
        price = self._prices.get(model)
        if price is None:
            raise UnknownModelError(f"no price configured for model {model!r}")
        billed = usage.input_tokens * price.input_per_mtok
        billed += usage.output_tokens * price.output_per_mtok
        return _ceil_div(billed, TOKENS_PER_MTOK)
