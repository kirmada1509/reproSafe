#!/usr/bin/env python3
"""Small local-only HTTP server and deterministic reproduction engine."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
from copy import deepcopy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).parent
FIXTURE_PATH = ROOT / "fixtures" / "northstar-invoice.json"
TARGET_CODE = "REPROSAFE_TARGET_FAILURE"
REQUIRED_TOP_LEVEL = {"metadata", "request", "expected", "observed", "reproduction", "disclosure"}


def load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _get_path(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _valid_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_input(case: dict[str, Any]) -> str | None:
    """Return an input problem, or None when the case is executable."""
    missing = sorted(REQUIRED_TOP_LEVEL - set(case))
    if missing:
        return f"Missing required sections: {', '.join(missing)}"
    request = case.get("request")
    if not isinstance(request, dict):
        return "request must be an object"
    customer = request.get("customer")
    invoice = request.get("invoice")
    if not isinstance(customer, dict) or not isinstance(invoice, dict):
        return "request.customer and request.invoice must be objects"
    if not isinstance(customer.get("email"), str) or not customer["email"].strip():
        return "request.customer.email must be a non-empty string"
    if not isinstance(invoice.get("line_items"), list) or not invoice["line_items"]:
        return "request.invoice.line_items must be a non-empty list"
    for item in invoice["line_items"]:
        if not isinstance(item, dict) or not _valid_number(item.get("quantity")) or not _valid_number(item.get("unit_price")):
            return "each invoice line item needs numeric quantity and unit_price"
    return None


def execute_case(case: dict[str, Any], *, timeout_ms: int | None = None) -> dict[str, Any]:
    """Run the fictional service and classify the observed outcome.

    This function intentionally models a deterministic service locally. It never
    reads the original fixture from outside the process and never makes a network
    request.
    """
    started = time.perf_counter()
    invalid = validate_input(case)
    if invalid:
        return _result("invalid-input", "Input rejected", invalid, started)

    metadata = case.get("metadata", {})
    dependencies = metadata.get("dependencies", [])
    if "__missing_dependency__" in dependencies:
        return _result("missing-dependency", "Dependency unavailable", "The declared local dependency is not installed.", started)
    if metadata.get("simulate_timeout"):
        budget = timeout_ms if timeout_ms is not None else case.get("reproduction", {}).get("timeout_ms", 500)
        if budget < 1000:
            return _result("timeout", "Execution timed out", f"The local runner stopped after {budget} ms.", started)

    email = case["request"]["customer"]["email"].strip().lower()
    # The fictional defect is triggered by the .example tenant domain. The
    # exact customer value is not required; preserving this shape is enough.
    target_triggered = email.endswith(".example")
    if target_triggered:
        return _result(
            "target-failure",
            "Target failure reproduced",
            "The parser error returned REPROSAFE_TARGET_FAILURE.",
            started,
            details={"error_code": TARGET_CODE, "expected_status": 200, "observed_status": 500},
        )

    total = sum(item["quantity"] * item["unit_price"] for item in case["request"]["invoice"]["line_items"])
    return _result(
        "success",
        "Successful input",
        "The invoice total was calculated without the target failure.",
        started,
        details={"status": 200, "total": round(total, 2)},
    )


def _result(kind: str, label: str, message: str, started: float, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "kind": kind,
        "label": label,
        "message": message,
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        "details": details or {},
    }


def compact_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def case_size(case: dict[str, Any]) -> int:
    """Return the exact UTF-8 byte size used for reduction comparisons."""
    return len(compact_json(case).encode("utf-8"))


def _leaf_paths(value: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(child, (dict, list)):
                paths.extend(_leaf_paths(child, path))
            else:
                paths.append(path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            path = f"{prefix}[{index}]"
            if isinstance(child, (dict, list)):
                paths.extend(_leaf_paths(child, path))
            else:
                paths.append(path)
    return paths


def _remove_path(case: dict[str, Any], path: str) -> dict[str, Any]:
    """Remove one leaf from a JSON case without mutating the supplied case."""
    candidate = deepcopy(case)
    parts = path.replace("]", "").replace("[", ".").split(".")
    current: Any = candidate
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    last = parts[-1]
    if isinstance(current, list):
        current.pop(int(last))
    else:
        current.pop(last, None)
    return candidate


def reduce_case(case: dict[str, Any], *, cancel_after: int | None = None) -> dict[str, Any]:
    """Greedily remove leaf values, accepting only checked target failures.

    This is a practical reduction report, not a proof of mathematical minimality.
    Every accepted candidate has an execution result recorded in ``checks``.
    """
    original = deepcopy(case)
    baseline = execute_case(original)
    original_size = case_size(original)
    if baseline["kind"] != "target-failure":
        return {
            "status": "not-reducible",
            "original_size": original_size,
            "candidate": original,
            "candidate_size": original_size,
            "attempts": 0,
            "accepted": 0,
            "checks": [],
            "message": "Reduction requires a reproduced target failure.",
        }

    current = deepcopy(original)
    checks: list[dict[str, Any]] = []
    accepted = 0
    paths = [
        path for path in _leaf_paths(current)
        if path not in {"request.customer.email", "request.invoice.line_items[0].quantity", "request.invoice.line_items[0].unit_price"}
    ]
    for path in paths:
        if cancel_after is not None and len(checks) >= cancel_after:
            return {
                "status": "cancelled",
                "original_size": original_size,
                "candidate": original,
                "candidate_size": original_size,
                "attempts": len(checks),
                "accepted": 0,
                "checks": checks,
                "message": "Reduction cancelled; the original input remains the candidate.",
            }
        if _get_path(current, path) is None:
            continue
        trial = _remove_path(current, path)
        result = execute_case(trial)
        accepted_trial = result["kind"] == "target-failure"
        check = {
            "path": path,
            "accepted": accepted_trial,
            "result": result["kind"],
            "size_before": case_size(current),
            "size_after": case_size(trial),
        }
        checks.append(check)
        if accepted_trial:
            current = trial
            accepted += 1

    candidate_size = case_size(current)
    return {
        "status": "completed",
        "original_size": original_size,
        "candidate": current,
        "candidate_size": candidate_size,
        "attempts": len(checks),
        "accepted": accepted,
        "checks": checks,
        "message": f"Accepted {accepted} checked reductions; this candidate is not claimed to be mathematically minimal.",
    }


def _set_path(case: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current: Any = case
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return
        current = current[part]
    if isinstance(current, dict) and parts[-1] in current:
        current[parts[-1]] = value


def _get_original_values(case: dict[str, Any], paths: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for path in paths:
        value = _get_path(case, path)
        if value is not None:
            values[path] = value
    return values


def disclosure_check(original: dict[str, Any], proposed: dict[str, Any], paths: list[str]) -> dict[str, Any]:
    """Check configured exact sensitive values, not universal anonymity."""
    proposed_text = compact_json(proposed)
    original_values = _get_original_values(original, paths)
    leaked = [path for path, value in original_values.items() if str(value) in proposed_text]
    checked = [path for path in original_values if path not in leaked]
    return {
        "kind": "passed" if not leaked else "failed",
        "label": "Configured disclosure checks passed" if not leaked else "Configured disclosure checks failed",
        "checked_paths": checked,
        "leaked_paths": leaked,
        "message": "Configured exact values are absent from the proposed JSON." if not leaked else "One or more configured original values are still present.",
        "scope": "Exact configured values only; this does not prove universal anonymity.",
    }


def transform_case(case: dict[str, Any], paths: list[str], strategy: str) -> dict[str, Any]:
    """Apply one of the two supported fictional-data transformations."""
    transformed = deepcopy(case)
    replacements = {
        "request.customer.name": "Demo Customer",
        "request.customer.email": "synthetic@northstar.example",
        "request.customer.account_id": "acct_reprosafe_demo",
        "request.payment.card_last4": "0000",
    }
    for path in paths:
        if strategy == "redact":
            _set_path(transformed, path, "[REDACTED]")
        elif strategy == "synthetic":
            _set_path(transformed, path, replacements.get(path, "synthetic-value"))
        else:
            raise ValueError(f"Unsupported transformation strategy: {strategy}")
    return transformed


def transform_case_report(case: dict[str, Any], paths: list[str], strategy: str) -> dict[str, Any]:
    proposed = transform_case(case, paths, strategy)
    reproduction = execute_case(proposed)
    disclosure = disclosure_check(case, proposed, paths)
    acceptable = reproduction["kind"] == "target-failure" and disclosure["kind"] == "passed"
    return {
        "strategy": strategy,
        "label": "Ordinary redaction" if strategy == "redact" else "Structure-preserving synthetic values",
        "case": proposed,
        "reproduction": reproduction,
        "disclosure": disclosure,
        "acceptable": acceptable,
        "message": "Accepted candidate: both checks pass." if acceptable else "Not an acceptable export candidate: both reproducibility and disclosure checks must pass.",
    }


def _replay_script() -> str:
    return '''#!/usr/bin/env python3
"""ReproSafe clean-environment replay; standard library only."""
import argparse
import json


def run(request, fixed=False):
    email = request["customer"]["email"].strip().lower()
    total = sum(item["quantity"] * item["unit_price"] for item in request["invoice"]["line_items"])
    if not fixed and email.endswith(".example"):
        return {"status": 500, "error_code": "REPROSAFE_TARGET_FAILURE", "message": "billing context could not be parsed"}
    return {"status": 200, "total": round(total, 2), "currency": request["invoice"]["currency"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="request.json")
    parser.add_argument("--fixed", action="store_true", help="replay after the fictional defect is fixed")
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as handle:
        request = json.load(handle)
    print(json.dumps(run(request, fixed=args.fixed), indent=2, sort_keys=True))
'''


def replay_result(request: dict[str, Any], *, fixed: bool = False) -> dict[str, Any]:
    """Run the same logic embedded in the exported clean replay."""
    email = request["customer"]["email"].strip().lower()
    total = sum(item["quantity"] * item["unit_price"] for item in request["invoice"]["line_items"])
    if not fixed and email.endswith(".example"):
        return {"status": 500, "error_code": TARGET_CODE, "message": "billing context could not be parsed"}
    return {"status": 200, "total": round(total, 2), "currency": request["invoice"]["currency"]}


def _export_files(case: dict[str, Any], paths: list[str], strategy: str) -> tuple[dict[str, bytes], dict[str, Any]]:
    transformed = transform_case(case, paths, strategy)
    reproduction = execute_case(transformed)
    disclosure = disclosure_check(case, transformed, paths)
    if reproduction["kind"] != "target-failure" or disclosure["kind"] != "passed":
        raise ValueError("No acceptable transformed candidate is available for export")
    request_text = compact_json(transformed["request"])
    replay = _replay_script()
    # The replay's --fixed behavior is intentionally recorded separately from
    # the defect-mode local execution. It must return the expected 200 result.
    fixed_result = replay_result(transformed["request"], fixed=True)
    if fixed_result["status"] != 200:
        raise ValueError("The clean replay did not pass in fixed mode")
    expected_total = fixed_result["total"]
    evidence = {
        "report_version": "1",
        "target": "REPROSAFE_TARGET_FAILURE",
        "reproduction": {"status": "passed", "classification": reproduction["kind"], "error_code": reproduction["details"]["error_code"]},
        "fixed_reproduction": {"status": "passed", "classification": "success", "expected_status": 200, "expected_total": expected_total},
        "disclosure": {"status": disclosure["kind"], "checked_paths": disclosure["checked_paths"], "leaked_paths": disclosure["leaked_paths"]},
        "retained_information": ["request shape", "invoice line-item arithmetic", "target domain shape (.example)", "reproduction steps"],
        "limits": ["Checks only configured exact sensitive values.", "A passing report does not prove universal anonymity.", "The replay is a fictional standard-library simulator, not the original production service."],
        "original_input_included": False,
    }
    manifest = {
        "format": "reprosafe-package/v1",
        "strategy": strategy,
        "files": ["README.txt", "request.json", "replay.py", "evidence-report.json", "manifest.json"],
        "original_input_included": False,
    }
    readme = """ReproSafe verified reproduction\n\nRun in Python 3.12+:\n  python3 replay.py --input request.json\n\nThe command should return HTTP 500 with REPROSAFE_TARGET_FAILURE.\nTo replay after the demonstrated fictional defect is fixed:\n  python3 replay.py --input request.json --fixed\n\nThe fixed command should return HTTP 200 and total 199.00.\nSee evidence-report.json for the checks and their limits.\n"""
    files = {
        "README.txt": readme.encode("utf-8"),
        "request.json": request_text.encode("utf-8"),
        "replay.py": replay.encode("utf-8"),
        "evidence-report.json": compact_json(evidence).encode("utf-8"),
        "manifest.json": compact_json(manifest).encode("utf-8"),
    }
    return files, evidence


def build_export(case: dict[str, Any], paths: list[str], strategy: str = "synthetic") -> tuple[bytes, dict[str, Any]]:
    files, evidence = _export_files(case, paths, strategy)
    output = io.BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name in sorted(files):
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, files[name])
    return output.getvalue(), evidence


def export_review(case: dict[str, Any], paths: list[str], strategy: str = "synthetic") -> dict[str, Any]:
    files, evidence = _export_files(case, paths, strategy)
    return {
        "filename": "reprosafe-northstar-verified.zip",
        "files": [{"name": name, "bytes": len(content), "purpose": {
            "README.txt": "exact clean-environment commands",
            "request.json": "transformed request only",
            "replay.py": "standard-library fictional replay",
            "evidence-report.json": "reproducibility, disclosure, retained information, and limits",
            "manifest.json": "package contents and safety boundary",
        }[name]} for name, content in sorted(files.items())],
        "outbound_summary": "Only the transformed request, replay instructions, supporting script, manifest, and evidence report leave this local environment.",
        "original_input_included": False,
        "evidence": evidence,
    }


class ReproSafeHandler(BaseHTTPRequestHandler):
    server_version = "ReproSafe/0.1"

    def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = compact_json(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/example":
            self._send_json({"case": load_fixture()})
        elif path == "/":
            self._send_file(ROOT / "static" / "index.html", "text/html; charset=utf-8")
        elif path == "/app.js":
            self._send_file(ROOT / "static" / "app.js", "text/javascript; charset=utf-8")
        elif path == "/styles.css":
            self._send_file(ROOT / "static" / "styles.css", "text/css; charset=utf-8")
        else:
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in {"/api/run", "/api/reduce", "/api/transform", "/api/export-review", "/api/export"}:
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            case = payload.get("case") if isinstance(payload, dict) else None
            if not isinstance(case, dict):
                raise ValueError("body.case must be an object")
            if path == "/api/run":
                timeout_ms = payload.get("timeout_ms")
                result = execute_case(case, timeout_ms=timeout_ms if isinstance(timeout_ms, int) else None)
                self._send_json({"result": result})
            else:
                if path == "/api/reduce":
                    cancel_after = payload.get("cancel_after")
                    report = reduce_case(case, cancel_after=cancel_after if isinstance(cancel_after, int) else None)
                    self._send_json({"report": report})
                else:
                    paths = payload.get("paths")
                    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
                        raise ValueError("body.paths must be a list of strings")
                    if path == "/api/transform":
                        self._send_json({
                            "reports": [
                                transform_case_report(case, paths, "redact"),
                                transform_case_report(case, paths, "synthetic"),
                            ]
                        })
                    else:
                        strategy = payload.get("strategy", "synthetic")
                        if not isinstance(strategy, str):
                            raise ValueError("body.strategy must be a string")
                        if path == "/api/export-review":
                            self._send_json({"review": export_review(case, paths, strategy)})
                        else:
                            package, evidence = build_export(case, paths, strategy)
                            self.send_response(HTTPStatus.OK)
                            self.send_header("Content-Type", "application/zip")
                            self.send_header("Content-Disposition", 'attachment; filename="reprosafe-northstar-verified.zip"')
                            self.send_header("X-ReproSafe-Evidence", hashlib.sha256(compact_json(evidence).encode()).hexdigest())
                            self.send_header("Content-Length", str(len(package)))
                            self.end_headers()
                            self.wfile.write(package)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep the local demo quiet; errors still surface in the UI response.
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local ReproSafe workbench")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ReproSafeHandler)
    print(f"ReproSafe listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping ReproSafe")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
