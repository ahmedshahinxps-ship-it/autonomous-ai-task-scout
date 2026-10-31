# Autonomous AI Task Scout — v0.1

**Current status: read-only automated discovery, not a revenue-producing agent.** The scanner never claims tasks, submits bids, executes instructions from listings, or interacts with payment accounts.

## What is deployed

- `scout.py` scans the public Jobbi gigs JSON feed and selects USD agent-lane leads above $20.
- `tests/test_scout.py` tests filters, safety, expiration, and disabled submissions.
- `.github/workflows/task-scout.yml` runs the tests and scout daily at **07:17 UTC**, and supports manual runs.
- Successful live scans upload `daily-opportunity-report` with `index.html` and `opportunities.json` to the **Actions → run → Artifacts** section.

To test immediately, open **Actions → Free Read-Only Task Scout → Run workflow**. A scheduled run may be delayed and can be disabled by GitHub after extended inactivity.

The public JSON feed may change or be temporarily unavailable. In that case the run will fail rather than present fictional tasks as real. The scanner uses Python's standard library and no paid API. No guarantees of free usage forever.

## Payment preferences

1. Your own QNB Egypt USD account where a platform supports reasonable USD payout fees.
2. Your own QNB or NBE Egypt EGP account.
3. Trusted Saudi contact only as a platform-permitted backup.

**No eligible payer, payout, or automatic task acceptance has been verified by this prototype.** Keep all bank details and credentials out of the public repository.

## Next phases (not yet deployed)

Verify funded bounties, AI participation permissions, Egyptian payout eligibility and objective acceptance conditions; sandbox an agent to test code/data tasks; only then consider auto-submission on explicitly compatible platforms.

Run locally:

```bash
python -m unittest discover -s tests -v
python scout.py --output output
```

The reports contain unverified opportunity leads, not earnings. Fit scores are simple keyword-based rankings, not probabilities of acceptance.
