# ReproSafe

> **Share the bug without sharing the customer data.**

ReproSafe is a local-first developer tool for turning a bug involving sensitive data into a small, shareable reproduction that still demonstrates the original failure. It preserves the original fixture, reduces only through checked executions, applies explicit disclosure rules, and exports a clean replay plus evidence.

## Buildathon deliverable

This project targets the **OmniRush Frontier Buildathon — Developer Tools & Open Source** track. It is intentionally focused rather than a general-purpose sandbox:

- **Input:** JSON request fixtures with expected/observed behavior, reproduction steps, and configured sensitive paths.
- **Execution:** a deterministic fictional invoice-parser simulator running locally in Python; no arbitrary customer code is executed.
- **Transformations:** exact-value redaction and structure-preserving fictional replacements.
- **Export:** a ZIP containing a transformed request, standard-library replay, instructions, manifest, and evidence report.
- **Supported environments:** Python 3.12+ and a modern browser; Docker provides the clean supported environment.
- **No external model requests:** original data processing stays local. This demo uses no model provider, API key, or network service.

The limitations are deliberate: the current product does not execute arbitrary production commands, understand every serialization format, discover every possible sensitive value, prove universal anonymity, or reproduce a real production service without an adapter. A passing configured disclosure check means only that the configured exact values were absent from the checked JSON.

## User journey

The main workflow is organized as **Reproduce → Reduce → Transform → Review & Export**.

1. **Reproduce:** load the fictional Northstar Billing example and run it repeatedly. The runner distinguishes `target-failure`, `success`, `invalid-input`, `missing-dependency`, and `timeout`.
2. **Reduce:** greedily try removing JSON leaves. Every accepted change is executed again; the report shows byte sizes, attempts, and accepted checks. The result is not claimed to be mathematically minimal.
3. **Transform:** select sensitive paths. Ordinary `[REDACTED]` demonstrates that a naive transformation can remove the failure. Synthetic values preserve the `.example` trigger while removing configured original values.
4. **Review & Export:** inspect the exact five outbound files, then download a ZIP. The included replay demonstrates defect mode and `--fixed` mode independently.

## Demo walkthrough

```text
Run example
  → Target failure reproduced / REPROSAFE_TARGET_FAILURE
Reduce example
  → 1,643 bytes → 992 bytes; accepted reductions remain checked
Check transformations
  → redaction: disclosure passed, target failure absent
  → synthetic values: disclosure passed, target failure reproduced
Review & Export
  → inspect README.txt, request.json, replay.py, evidence-report.json, manifest.json
Download verified package
  → run replay.py normally and with --fixed in a clean Python environment
```

The app uses fictional values only: `Maya Iyer`, `maya.iyer@northstar.example`, `acct_fictional_48291`, and `4242` are demonstration data, not customer data.

## Setup

Requirements:

- Python 3.12+ (the repository pins the intended version in `.python-version`)
- Node 22.14+ only if you want to run the JavaScript syntax check (pinned in `.nvmrc`)
- Docker 24+ for the container path

No third-party Python or JavaScript dependencies are required. `package-lock.json` is kept with `package.json` for reproducibility even though the browser app uses no npm packages.

```bash
git clone <repository-url> reproSafe
cd reproSafe
cp .env.example .env       # optional; the app needs no secrets
```

## Run locally

```bash
python3 server.py
```

Open <http://127.0.0.1:4173>. The server binds to loopback by default and serves the UI plus local JSON endpoints. To choose a port or bind for a container:

```bash
python3 server.py --host 0.0.0.0 --port 4173
```

## Test offline

The single project test command uses only the Python standard library and does not contact the network:

```bash
make test
```

It covers deterministic classification, repeated reproduction, invalid/missing-dependency/timeout separation, checked reduction, cancellation, disclosure behavior, export safety, and independent defect/fixed replay.

Additional syntax checks used during development:

```bash
python3 -m py_compile server.py tests/test_engine.py
node --check static/app.js
```

## Docker build, run, and deploy

Build and run the clean supported image:

```bash
docker build -t reprosafe:local .
docker run --rm -p 4173:4173 reprosafe:local
```

Open <http://127.0.0.1:4173>. For an OCI deployment, push the same image to the deployment registry and run it with port `4173` exposed; no runtime secrets or database are required:

```bash
docker tag reprosafe:local registry.example/reprosafe:1.0.0
docker push registry.example/reprosafe:1.0.0
docker run --rm -p 4173:4173 registry.example/reprosafe:1.0.0
```

The registry hostname above is a placeholder; deployment credentials and registry policy belong to the deployment environment, not this repository.

## Safety and evidence boundary

- Original inputs remain in the local process and are not sent to an external model or service.
- The fixture is copied before reduction and transformations; cancellation leaves the original candidate intact.
- Export names and generated reports contain no original fixture values in the demonstrated flow.
- The evidence report documents retained information and limits.
- Configured disclosure checks are exact-value checks over the proposed JSON. They do **not** detect every inference, derived identifier, sensitive value in an unconfigured path, or universal anonymity.

## Submission checklist

The repository includes the buildathon requirements that can be verified locally: a usable end-to-end demo, fictional data, local-only processing, clear scope and limits, accessible status-driven UI, pinned runtime files, a lockfile, Dockerfile, offline `make test`, and this README with setup/run/test/deploy/reproduction instructions. No public official Frontier Buildathon checklist was discoverable from the available search results; if the event organizer publishes additional submission metadata or a deadline-specific form, verify that separately before submission.
