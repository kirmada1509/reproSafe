# ReproSafe submission verification

Checked on 2026-10-18 against the requested Frontier Buildathon brief and the repository's local checks.

| Requirement | Evidence | Status |
|---|---|---|
| Developer Tools & Open Source focus | Local-first bug reproduction workbench | Pass |
| Fictional sensitive data only | `fixtures/northstar-invoice.json` | Pass |
| Original input preserved | deep-copy reduction/transform engine and read-only UI | Pass |
| No external model request for original data | standard-library local server; no provider config | Pass |
| Reproduce deterministic target failure | `execute_case` and repeated test | Pass |
| Distinguish unrelated execution outcomes | invalid, missing dependency, timeout tests | Pass |
| Reduce with per-acceptance execution checks | `reduce_case` report and UI check list | Pass |
| Cancellation keeps original intact | cancellation test and UI controller | Pass |
| Disclosure checks separate from reproducibility | two result columns/cards | Pass |
| Redaction removes the bug | redaction test and demo card | Pass |
| Alternative transformation preserves the bug | synthetic-value test and demo card | Pass |
| Honest no-candidate result | engine/UI message | Pass |
| Review exact outbound files | `/api/export-review` and review panel | Pass |
| Independent clean replay | ZIP extraction subprocess test | Pass |
| Replay passes after fictional fix | `replay.py --fixed` test | Pass |
| Evidence states limits | `evidence-report.json` | Pass |
| Empty/loading/cancelled/failed/completed states | UI status banner and action states | Pass |
| Keyboard/focus/contrast basics | semantic controls, focus-visible CSS, text + icon statuses | Pass |
| Docker rebuild | `Dockerfile`; local `docker build` attempted | Blocked: Docker daemon unavailable in this workspace |
| Offline single test command | `Makefile` → `make test` | Pass |
| Pinned runtime and lockfile | `.python-version`, `.nvmrc`, `package-lock.json` | Pass |

The event name and track were supplied in the brief. A public official checklist page was not found by the available web search, so this table does not invent organizer-specific requirements.
