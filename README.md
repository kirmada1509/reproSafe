# ReproSafe

> Share the bug without sharing the customer data.

ReproSafe is a local-first workbench for turning a sensitive bug report into a small, shareable reproduction. The initial demonstration uses a fully fictional Northstar Billing JSON fixture and a deterministic local simulator. Original inputs stay local; no external model or network request is needed.

## Current checkpoint: Phase 1

The first checkpoint delivers **Reproduce**:

- load the fictional Northstar invoice parser example immediately;
- inspect the request, expected response, and observed response;
- run the example repeatedly through the local deterministic engine;
- classify the target failure, a successful input, invalid input, a missing dependency, and a timeout separately;
- preserve the original fixture as read-only input.

Reduction, disclosure transformations, review, and export are intentionally not enabled yet. The footer explicitly says disclosure checks have not run.

## Supported scope

The focused initial scope is JSON request fixtures executed by ReproSafe's local simulator. The simulator understands invoice line items, a customer email trigger, and the target marker `REPROSAFE_TARGET_FAILURE`. It is a demonstrator for the full workflow, not a general-purpose sandbox for arbitrary customer programs.

Supported environments are Python 3.12+ for the local server and modern browsers with `fetch`, `details`, and ES2020 JavaScript support. A Docker image is provided for a clean supported environment.

Limitations at this checkpoint: only the fictional fixture and deterministic simulator are wired into the UI; no arbitrary command execution, real customer data, external integrations, universal anonymity guarantee, or export package exists yet.

## Run locally

```bash
python3 server.py
```

Open <http://127.0.0.1:4173>. Click **Run example**. A successful phase-1 run shows **Target failure reproduced** and `target-failure` with the `REPROSAFE_TARGET_FAILURE` evidence.

## Test

The test command is offline and uses only the Python standard library:

```bash
make test
```

## Docker

```bash
docker build -t reprosafe .
docker run --rm -p 4173:4173 reprosafe
```

Then open <http://127.0.0.1:4173>.

## Safety boundary

This project contains fictional data only. Passing a configured disclosure check will never prove universal anonymity; later evidence reports will document exactly which configured values and paths were checked.
