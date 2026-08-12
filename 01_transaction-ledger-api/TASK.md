# Task 01 — Transaction Ledger API

**Domain:** Software Engineering Foundations
**Goal:** a small service, built to a standard you could put in front of a hiring
manager and not flinch. This isn't about the ledger logic being clever — it's
about every foundational habit (typing, tests, git, containerization, CI,
API design, SQL) showing up in one coherent piece of work.

## The brief

Build an HTTP API for a simple transaction ledger. Accounts have a balance.
Transactions move money between an external source and an account, or between
two accounts.

### Required endpoints

- `POST /accounts` — create an account (starts at balance 0).
- `GET /accounts/{id}` — fetch an account and its current balance.
- `POST /transactions` — create a transaction. Body includes at minimum:
  `from_account` (nullable — null means external deposit), `to_account`
  (nullable — null means external withdrawal), `amount` (positive, decimal-safe —
  do **not** use floats for money), and an `Idempotency-Key` header.
- `GET /transactions/{id}` — fetch a single transaction.
- `GET /transactions?account_id=&limit=&cursor=` — paginated list, filterable
  by account.

### Rules the implementation must actually enforce

1. **Idempotency**: replaying a `POST /transactions` with the same
   `Idempotency-Key` must return the original result, not create a second
   transaction. Different key + same body = a new, separate transaction.
2. **No overdraft**: a transaction that would take an account negative is
   rejected (`409` or `422` — your call, but be consistent and document it).
3. **Atomicity**: a transaction between two accounts either fully applies
   (both balances update) or not at all — no partial state on crash or
   concurrent access. This is the crux of the exercise; don't hand-wave it.
4. **Money is exact**: integer cents or `Decimal`, never `float`.
5. **Pagination is real**: `limit`/`cursor` must behave correctly at the
   boundaries (empty result, last page, invalid cursor).

### Non-negotiable technical constraints

- Python, `src/`-layout package, `pyproject.toml` (no bare `requirements.txt`
  as the only dependency source).
- Full type hints; the project should pass `mypy --strict` or you should be
  able to justify every `# type: ignore`.
- FastAPI (or equivalent) for the API layer.
- SQLite for storage — raw SQL or SQLAlchemy Core, not a full ORM. You should
  be able to explain the exact SQL your idempotency check and balance update
  run, including how you prevent a race between "check balance" and "apply
  transaction."
- `pytest` test suite covering: happy path, insufficient funds, duplicate
  idempotency key, invalid account, pagination edge cases. Use FastAPI's
  `TestClient` for the integration-level tests.
- `Dockerfile` — `docker build` + `docker run` should give a working API with
  no extra setup.
- GitHub Actions workflow: lint (`ruff`) + type check (`mypy`) + `pytest` on
  every push.
- Git history that reads like real work: incremental commits with real
  messages, not one "final commit."
- `README.md`: what it is, how to run it (local + Docker), and how to run the
  tests.

### Explicitly not required

- Auth/users — accounts are just IDs, no login.
- A frontend.
- Multi-currency.
- Deployment anywhere real — Docker running locally is enough.

### Stretch (optional, only after the above is solid)

- A small CLI client (`click` or `argparse`) that talks to the API.
- Load-test the concurrent-transaction path (e.g. with `pytest-asyncio` +
  concurrent requests) and show it holds up.
- Structured logging (`structlog` or stdlib `logging` with a JSON formatter).

## When you're done

Don't over-polish past what's asked — ship it, then come back and ask for a
review. I'll check it against the rules above (especially the atomicity and
idempotency behavior, since those are the two places shortcuts usually hide),
plus general code quality, test quality, and git hygiene, and tell you
straight where it stands against a real mid-level bar.
