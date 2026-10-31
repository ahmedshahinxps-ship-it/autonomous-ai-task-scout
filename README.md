# Autonomous AI Task Scout — v0.2

**Live deployment:** Automated read-only bounty discovery and preliminary GitHub issue verification. **No paid work has been submitted, accepted, or paid.**

## Automated workflow

The [GitHub Actions workflow](https://github.com/ahmedshahinxps-ship-it/autonomous-ai-task-scout/actions) runs each day at **07:17 UTC**, on relevant code pushes, and via optional manual dispatch. Your laptop does not have to remain on.

1. **Discovery:** `scout.py` reads Jobbi's JSON feed and ranks USD agent-lane bounty listings.
2. **Vetting:** `vet.py` examines up to 12 narrowly scoped documentation, data, or testing GitHub issues per scan. It checks public GitHub metadata for open/closed, locked, assignees, high comment volume, issue age and activity. The public API is rate-limited, and checks may remain unverified if GitHub is unavailable.
3. **Quality:** `python -m unittest discover -s tests -v` runs offline security and filter tests.
4. **Reporting:** The successful workflow attaches a ZIP containing `index.html`, `opportunities.json`, `vetting.html`, and `vetting.json`.

**First v0.2 run (October 31, 2026):** 10 candidate GitHub issues checked, zero passed basic checks. These figures do not reflect guaranteed opportunities.

## Important constraints

- No task claims, submissions, proposals, messages or payments occur.
- A **preliminary-review** result means only that a GitHub issue appears open and recent. It does **not** establish permission for AI-generated work, confirmed escrow, acceptance or compatibility with Egyptian payout accounts.
- The ranking is heuristic, not a probability of earning money.
- Incoming listing content is treated as untrusted data. No task instructions are executed.
- The public repository must not contain banking details, personal credentials, or API keys.

## Payment preference (not configured or verified)

1. Personal QNB Egypt USD account, if a marketplace supports direct, economical USD settlement.
2. Personal QNB/NBE EGP account.
3. Saudi contact only as a platform-permitted fallback.

## Remaining work

Find credible fresh funded opportunities; verify automation rules and country-specific payout eligibility; then build task-specific execution and independent tests. Automatic paid submissions should not be enabled until these have been demonstrated.

## Local commands

```bash
python -m unittest discover -s tests -v
python scout.py --output output
python vet.py --input output/opportunities.json --output output --max-checks 12
```
