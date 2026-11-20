"""Gateway: reserve budget, call the provider, record the real cost."""

from .budget import Budgets
from .ledger import Entry, Ledger
from .pricing import PriceTable
from .provider import Provider, Request, Response, Usage, estimate_tokens


class BudgetedGateway:
    def __init__(
        self, provider: Provider, prices: PriceTable, budgets: Budgets, ledger: Ledger
    ) -> None:
        self._provider = provider
        self._prices = prices
        self._budgets = budgets
        self._ledger = ledger

    def complete(self, key: str, request: Request) -> Response:
        # Worst case: the whole prompt billed, and the reply fills max_tokens.
        worst_case = self._prices.cost(
            request.model, Usage(estimate_tokens(request.prompt), request.max_tokens)
        )
        self._budgets.reserve(key, worst_case)
        try:
            response = self._provider.complete(request)
            actual = self._prices.cost(response.model, response.usage)
        except Exception:
            self._budgets.release(key, worst_case)
            raise
        self._budgets.settle(key, worst_case, actual)
        self._ledger.record(
            Entry(
                key,
                response.model,
                response.usage.input_tokens,
                response.usage.output_tokens,
                actual,
            )
        )
        return response
