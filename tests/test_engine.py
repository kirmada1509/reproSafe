import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from server import build_export, case_size, disclosure_check, execute_case, load_fixture, reduce_case, transform_case_report


class ReproductionEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture()

    def test_fixture_reproduces_target_failure_repeatedly(self):
        results = [execute_case(copy.deepcopy(self.fixture)) for _ in range(5)]

        self.assertTrue(all(result["kind"] == "target-failure" for result in results))
        self.assertTrue(all(result["details"]["error_code"] == "REPROSAFE_TARGET_FAILURE" for result in results))

    def test_successful_input_is_not_mistaken_for_target_failure(self):
        case = copy.deepcopy(self.fixture)
        case["request"]["customer"]["email"] = "maya.iyer@northstar.test"

        result = execute_case(case)

        self.assertEqual(result["kind"], "success")
        self.assertEqual(result["details"]["status"], 200)
        self.assertEqual(result["details"]["total"], 199.0)

    def test_invalid_input_is_classified_separately(self):
        case = copy.deepcopy(self.fixture)
        del case["request"]["customer"]["email"]

        result = execute_case(case)

        self.assertEqual(result["kind"], "invalid-input")
        self.assertNotEqual(result["kind"], "target-failure")

    def test_missing_dependency_is_classified_separately(self):
        case = copy.deepcopy(self.fixture)
        case["metadata"]["dependencies"].append("__missing_dependency__")

        result = execute_case(case)

        self.assertEqual(result["kind"], "missing-dependency")

    def test_timeout_is_classified_separately(self):
        case = copy.deepcopy(self.fixture)
        case["metadata"]["simulate_timeout"] = True

        result = execute_case(case, timeout_ms=500)

        self.assertEqual(result["kind"], "timeout")

    def test_fixture_is_valid_json_and_has_disclosure_paths(self):
        fixture_path = Path(__file__).parents[1] / "fixtures" / "northstar-invoice.json"
        parsed = json.loads(fixture_path.read_text(encoding="utf-8"))

        self.assertEqual(parsed, self.fixture)
        self.assertEqual(len(parsed["disclosure"]["sensitive_paths"]), 4)

    def test_reduction_accepts_only_checked_target_failures_and_gets_smaller(self):
        report = reduce_case(self.fixture)

        self.assertEqual(report["status"], "completed")
        self.assertLess(report["candidate_size"], report["original_size"])
        self.assertGreater(report["accepted"], 0)
        self.assertEqual(execute_case(report["candidate"])["kind"], "target-failure")
        self.assertTrue(all(check["accepted"] for check in report["checks"] if check["accepted"]))
        self.assertTrue(all(check["result"] == "target-failure" for check in report["checks"] if check["accepted"]))

    def test_cancelled_reduction_keeps_original_candidate(self):
        original = json.loads(json.dumps(self.fixture))
        report = reduce_case(original, cancel_after=1)

        self.assertEqual(report["status"], "cancelled")
        self.assertEqual(report["candidate"], original)
        self.assertEqual(report["candidate_size"], case_size(original))
        self.assertEqual(report["accepted"], 0)

    def test_redaction_passes_disclosure_but_removes_target_failure(self):
        paths = self.fixture["disclosure"]["sensitive_paths"]
        report = transform_case_report(self.fixture, paths, "redact")

        self.assertEqual(report["reproduction"]["kind"], "success")
        self.assertEqual(report["disclosure"]["kind"], "passed")
        self.assertFalse(report["acceptable"])

    def test_synthetic_values_pass_disclosure_and_preserve_target_failure(self):
        paths = self.fixture["disclosure"]["sensitive_paths"]
        report = transform_case_report(self.fixture, paths, "synthetic")

        self.assertEqual(report["reproduction"]["kind"], "target-failure")
        self.assertEqual(report["disclosure"]["kind"], "passed")
        self.assertTrue(report["acceptable"])
        self.assertNotIn(self.fixture["request"]["customer"]["email"], json.dumps(report["case"]))

    def test_unconfigured_sensitive_value_fails_the_configured_check(self):
        paths = ["request.customer.name"]
        disclosure = disclosure_check(self.fixture, self.fixture, paths)

        self.assertEqual(disclosure["kind"], "failed")
        self.assertEqual(disclosure["leaked_paths"], paths)

    def test_export_is_safe_and_replays_in_defect_and_fixed_modes(self):
        paths = self.fixture["disclosure"]["sensitive_paths"]
        package, evidence = build_export(self.fixture, paths)
        original_email = self.fixture["request"]["customer"]["email"]

        with ZipFile(io.BytesIO(package)) as archive:
            names = sorted(archive.namelist())
            self.assertEqual(names, ["README.txt", "evidence-report.json", "manifest.json", "replay.py", "request.json"])
            all_bytes = b"".join(archive.read(name) for name in names)
            self.assertNotIn(original_email.encode(), all_bytes)
            with tempfile.TemporaryDirectory() as temp_dir:
                archive.extractall(temp_dir)
                defect = subprocess.run([sys.executable, "replay.py", "--input", "request.json"], cwd=temp_dir, text=True, capture_output=True, check=True)
                fixed = subprocess.run([sys.executable, "replay.py", "--input", "request.json", "--fixed"], cwd=temp_dir, text=True, capture_output=True, check=True)

        self.assertEqual(json.loads(defect.stdout)["error_code"], "REPROSAFE_TARGET_FAILURE")
        self.assertEqual(json.loads(fixed.stdout)["status"], 200)
        self.assertFalse(evidence["original_input_included"])

    def test_export_accepts_the_reduced_candidate(self):
        paths = self.fixture["disclosure"]["sensitive_paths"]
        reduced = reduce_case(self.fixture)["candidate"]

        package, evidence = build_export(reduced, paths)

        self.assertGreater(len(package), 0)
        self.assertEqual(evidence["fixed_reproduction"]["expected_total"], 199.0)


if __name__ == "__main__":
    unittest.main()
