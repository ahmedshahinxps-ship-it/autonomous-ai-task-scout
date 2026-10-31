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


## v0.4 status — October 31, 2026

[Latest successful workflow run](https://github.com/ahmedshahinxps-ship-it/autonomous-ai-task-scout/actions/runs/41194885040)

- Source-aware, freshness-aware rankings implemented. Important: the feed publication date is **not** proof the underlying GitHub issue is recent.
- 26 automated tests passed.
- 320 listings scanned; 150 ranked entries retained for further review.
- 6 narrow GitHub issues vetted against their original issue metadata; **0** passed the basic checks.
- No verified platform-specific right to submit AI-generated work and no confirmed Egypt-compatible payout for a specific task.
- **Revenue earned: $0.** No work has been submitted to a customer.
- Further engineering should be prioritised **only** after finding a suitable funded task, rather than optimising hypothetical task completion.

The GitHub workflow continues its read-only daily scan; it cannot independently guarantee new opportunities or future acceptance. Human authorisation/verification may still be necessary for a payment platform.



## v0.5 — three daily scans and change detection (October 31, 2026)

- Scheduled GitHub Actions scans now run at **07:17, 13:17, 19:17 UTC** every day (roughly 09:17, 15:17, 21:17 in Egypt during standard time). Actual run starts may be delayed by GitHub; DST shifts the local clock by an hour.
- `track.py` compares the current *shortlist* with the most recent prior report artifact and writes `new_leads.json` / `new_leads.html`. A listing counted as **newly shortlisted** is **not necessarily newly posted** or funded; the count is not revenue.
- Previous-artifact comparisons use GitHub Actions read permission; a cross-host artifact redirect is handled without sending GitHub bearer tokens to the download host.
- [Verified successful comparison run](https://github.com/ahmedshahinxps-ship-it/autonomous-ai-task-scout/actions/runs/41196473042): **0 new entries** compared with the prior shortlist. The job's automated tests and processing steps all passed.
- Separately, a ChatGPT recurring condition watch is configured after each scan to notify about new actionable leads or repeated workflow failures; silence means no meaningful change was reported, **not** that a payment occurred.

The project remains a **read-only prototype**, not an autonomous paid job submission business. It does not claim work, send proposals, perform buyer jobs or withdraw money.
