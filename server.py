#!/usr/bin/env python3
"""Small local-only HTTP server and deterministic reproduction engine."""

from __future__ import annotations

import argparse
import json
import re
import time
from copy import deepcopy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


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
        if path != "/api/run":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            case = payload.get("case") if isinstance(payload, dict) else None
            if not isinstance(case, dict):
                raise ValueError("body.case must be an object")
            timeout_ms = payload.get("timeout_ms")
            result = execute_case(case, timeout_ms=timeout_ms if isinstance(timeout_ms, int) else None)
            self._send_json({"result": result})
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"result": _result("execution-error", "Execution error", str(exc), time.perf_counter())}, HTTPStatus.BAD_REQUEST)

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
