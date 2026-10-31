# Autonomous AI Task Scout — v0.3

**Deployment status:** The free GitHub workflow now performs read-only task discovery, basic issue vetting, and an offline demonstration of a structured-data task. It has **not** claimed, completed, submitted or earned payment from any real bounty.

## What happens automatically

The [GitHub Actions workflow](https://github.com/ahmedshahinxps-ship-it/autonomous-ai-task-scout/actions) runs at **07:17 UTC daily**, and on code changes. The laptop can be switched off.

1. **Discover** — `scout.py` reads Jobbi's JSON feed and ranks USD-denominated agent-lane leads.
2. **Vet** — `vet.py` checks up to 12 narrow GitHub issues for being open, unlocked, unassigned, not excessively crowded, and recently maintained.
3. **Demo task** — `worker.py` cleans `examples/sample_products.csv`, normalising SKUs, product names and prices, removing exact duplicates, and rejecting invalid or conflicting rows.
4. **Test and report** — Unit tests run automatically. A successful scan attaches `daily-opportunity-report.zip` containing `index.html`, `opportunities.json`, `vetting.html`, `vetting.json`, `work_sample/cleaned_catalogue.csv`, and `work_sample/worker_audit.json`.

## First verified v0.3 run (October 31, 2026)

[See successful run](https://github.com/ahmedshahinxps-ship-it/autonomous-ai-task-scout/actions/runs/41193277613)

- 320 Jobbi listings matched initial feed filters.
- 10 narrow GitHub issue leads were inspected; all 10 were rejected by basic issue checks.
- The **synthetic catalogue task** read 8 records, accepted 3, removed 1 duplicate, and rejected 4 problematic rows.
- Revenue: **$0**. Buyer acceptance: **none**. Submissions: **disabled**.

The data worker has only proved it can complete this **limited, predetermined** task. It does not yet interpret arbitrary bounty descriptions or solve arbitrary code issues. It uses no paid AI inference and never executes instructions supplied by job listings.

## Unresolved business requirements

A genuine funded bounty must be **available**, must **permit AI automation**, must have objective acceptance requirements, and must pay through a route compatible with an account in the user's own name in Egypt. These are **not yet verified for any specific live task**.

Payment priority: direct QNB Egypt USD; then QNB/NBE EGP; Saudi contact only as a platform-permitted backup.

## Safe local commands

```bash
python -m unittest discover -s tests -v
python scout.py --output output
python vet.py --input output/opportunities.json --output output --max-checks 12
python worker.py --input examples/sample_products.csv --output output/work_sample
```

No secrets or bank details are required or stored. The public repository contains only demonstration data and program code.
