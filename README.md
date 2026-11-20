# llm-cost-ledger-budgets

A small gateway layer that puts a token and cost ledger and hard spend
budgets in front of any LLM provider. Stdlib Python, runs offline against a
deterministic fake provider.

- Every call goes through one `Provider.complete` seam.
- Each completed call is written to a ledger with its token usage and cost.
- Each key (team, tenant, feature) has a budget. The worst-case cost of a call
  is reserved before it is sent, so concurrent callers cannot overshoot.

## Usage

```python
from costledger.budget import Budgets
from costledger.gateway import BudgetedGateway
from costledger.ledger import Ledger
from costledger.pricing import Price, PriceTable
from costledger.provider import FakeProvider, Request

prices = PriceTable({"small": Price(input_per_mtok=500_000, output_per_mtok=1_500_000)})
ledger = Ledger()
gateway = BudgetedGateway(FakeProvider(), prices, Budgets({"team-a": 50_000}), ledger)

gateway.complete("team-a", Request("small", "Summarise this ticket", max_tokens=200))
print(ledger.total_micros("team-a"))
```

Swap `FakeProvider` for any object with `complete(request) -> Response`.

## Design notes

- **Integer micro-USD.** Prices are micro-USD per million tokens and costs
  round up, so the ledger never under-reports and sums never drift.
- **Reserve, then settle.** Before the call, the cost of the estimated prompt
  plus `max_tokens` of output is reserved. After it, the reservation is replaced
  by the real cost. A failed call releases the reservation.
- **Estimates are conservative only for output.** The prompt estimate is
  `ceil(chars / 4)`, which can undercount for some tokenizers; a real adapter
  should supply an exact count.
- **Unknown models and keys are refused**, not priced at zero.

## Validate

```
make validate
```

Runs the unit tests and `scripts/simulate.py`, which sends 800 calls from 16
threads at one 50,000 micro-USD budget with the fake provider and an
illustrative price table. It checks spend stays within the limit, the ledger
agrees with the budget, and each served call reached the provider exactly once.
In the run on this fixture 356 calls were served and 444 refused; the exact split
varies with thread timing, the checks do not.
