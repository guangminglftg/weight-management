import unittest

from chart import build_clickable_chart, build_weight_data, date_range
from database import HealthRepository
from ui import load_form_values, point_date_from_records
import tempfile


class ChartTests(unittest.TestCase):
    def test_each_weight_point_carries_its_date(self):
        chart = build_clickable_chart([
            {"date": "2026-09-20", "weight_kg": 72.4},
            {"date": "2026-09-21", "weight_kg": None},
            {"date": "2026-09-22", "weight_kg": 72.1},
        ])
        self.assertIn('data-date="2026-09-20"', chart)
        self.assertIn('data-date="2026-09-22"', chart)
        self.assertNotIn('data-date="2026-09-21"', chart)
        self.assertEqual(chart.count('role="button"'), 2)

    def test_date_range_and_missing_values(self):
        self.assertEqual(date_range("2026-09-20", "2026-09-22"), ["2026-09-20", "2026-09-21", "2026-09-22"])
        chart_data = build_weight_data([{"date": "2026-09-20", "weight_kg": 72.4}])
        self.assertEqual(chart_data.to_dict("records"), [{"date": "2026-09-20", "weight_kg": 72.4}])

    def test_empty_chart_is_explicit(self):
        chart_data = build_weight_data([])
        self.assertEqual(list(chart_data.columns), ["date", "weight_kg"])
        self.assertTrue(chart_data.empty)

    def test_click_index_maps_to_weight_record_date(self):
        records = [
            {"date": "2026-09-20", "weight_kg": 72.4},
            {"date": "2026-09-21", "weight_kg": None},
            {"date": "2026-09-22", "weight_kg": 72.1},
        ]
        self.assertEqual(point_date_from_records(records, 1), "2026-09-22")
        self.assertIsNone(point_date_from_records(records, 2))

    def test_form_values_load_saved_weight_and_journal(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = HealthRepository(f"{directory}/health.sqlite3")
            repository.save_weight("2026-09-18", 71.6)
            repository.save_journal("2026-09-18", "睡得很好，晚餐清淡。")

            self.assertEqual(load_form_values(repository, "2026-09-18"), (71.6, "睡得很好，晚餐清淡。"))


if __name__ == "__main__":
    unittest.main()
