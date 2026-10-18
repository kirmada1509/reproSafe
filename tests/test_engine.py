import copy
import json
import unittest
from pathlib import Path

from server import execute_case, load_fixture


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


if __name__ == "__main__":
    unittest.main()
