# llm-cost-ledger-budgets

A small gateway layer that puts a token and cost ledger and hard spend
budgets in front of any LLM provider. Stdlib Python, runs offline against a
deterministic fake provider.

- Every call goes through one `Provider.complete` seam.
- Each completed call is written to a ledger with its token usage and cost.
- Each key (team, tenant, feature) has a budget. The worst-case cost of a call
  is reserved before it is sent, so concurrent callers cannot overshoot.

Work in progress; usage and results are added as the pieces land.
