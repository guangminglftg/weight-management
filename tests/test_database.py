import tempfile
import unittest
from pathlib import Path

from database import HealthRepository


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.repository = HealthRepository(Path(self.tempdir.name) / "health.sqlite3")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_upserts_weight_and_journal_by_date(self):
        self.repository.save_weight("2026-09-23", 72.4)
        self.repository.save_weight("2026-09-23", 72.1)
        self.repository.save_journal("2026-09-23", "早餐吃了鸡蛋，心情不错。")
        self.repository.save_journal("2026-09-23", "早餐吃了鸡蛋，下午有点困。")

        self.assertEqual(self.repository.get_weights(), [{"record_date": "2026-09-23", "weight_kg": 72.1}])
        self.assertEqual(self.repository.get_daily_record("2026-09-23")["journal"], "早餐吃了鸡蛋，下午有点困。")

    def test_range_search_summary_and_merge(self):
        self.repository.save_weight("2026-09-20", 73)
        self.repository.save_weight("2026-09-23", 72.2)
        self.repository.save_journal("2026-09-21", "睡眠六小时，压力一般。")

        self.assertEqual(len(self.repository.get_weights("2026-09-20", "2026-09-22")), 1)
        self.assertEqual(self.repository.search_journals(keyword="压力")[0]["entry_date"], "2026-09-21")
        self.assertEqual(self.repository.summary()["change_kg"], -0.8)
        self.assertEqual(self.repository.daily_records()[1]["journal"], "睡眠六小时，压力一般。")

    def test_empty_journal_removes_existing_entry_and_limits_results(self):
        self.repository.save_journal("2026-09-20", "a")
        self.repository.save_journal("2026-09-20", "")
        for day in range(1, 4):
            self.repository.save_weight(f"2026-09-2{day}", 70 + day)

        self.assertEqual(self.repository.search_journals(), [])
        self.assertEqual(len(self.repository.get_weights(limit=2)), 2)

    def test_daily_record_can_be_loaded_back_into_the_form(self):
        self.repository.save_weight("2026-09-18", 71.6)
        self.repository.save_journal("2026-09-18", "那天睡得很好，晚餐清淡。")

        record = self.repository.get_daily_record("2026-09-18")

        self.assertEqual(record, {
            "date": "2026-09-18",
            "weight_kg": 71.6,
            "journal": "那天睡得很好，晚餐清淡。",
        })


if __name__ == "__main__":
    unittest.main()
