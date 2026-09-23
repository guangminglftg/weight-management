import json
import tempfile
import unittest
from pathlib import Path

from database import HealthRepository
from tools import execute_tool, execute_tool_json


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.repository = HealthRepository(Path(self.tempdir.name) / "health.sqlite3")
        self.repository.save_weight("2026-09-20", 73)
        self.repository.save_journal("2026-09-20", "睡眠不足，晚餐吃了面条。")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_tools_return_structured_read_only_data(self):
        self.assertEqual(execute_tool(self.repository, "get_weight_records", {})["count"], 1)
        self.assertEqual(
            execute_tool(self.repository, "search_health_journals", {"keyword": "睡眠"})["count"],
            1,
        )
        self.assertEqual(execute_tool(self.repository, "get_daily_health_record", {"date": "2026-09-20"})["weight_kg"], 73.0)

    def test_invalid_json_and_unknown_tool_are_safe(self):
        self.assertIn("error", json.loads(execute_tool_json(self.repository, "get_summary", "not-json")))
        self.assertIn("error", execute_tool(self.repository, "DROP TABLE health_journal_entries", {}))
        self.assertEqual(self.repository.search_journals()[0]["content"], "睡眠不足，晚餐吃了面条。")


if __name__ == "__main__":
    unittest.main()
