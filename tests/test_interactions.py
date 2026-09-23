import tempfile
import unittest
from unittest.mock import patch

import app
from database import HealthRepository


class InteractionTests(unittest.TestCase):
    def test_click_edit_save_and_reload_date(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = HealthRepository(directory + "/health.sqlite3")
            repository.save_weight("2026-09-22", 72.5)
            repository.save_journal("2026-09-22", "原来的日志")
            with patch.object(app, "repository", repository):
                event = app.gr.SelectData(None, {"index": "2026-09-22", "value": "2026-09-22"})
                self.assertEqual(app.select_chart_point(event), ("2026-09-22", 72.5, "原来的日志"))
                result = app.save_record("2026-09-22 00:00:00", 72.3, "修改后的日志", "2026-09-17 00:00:00", "2026-09-23 00:00:00")
                self.assertEqual(result[0], "已保存")
                self.assertEqual(app.load_record("2026-09-23 00:00:00"), (None, ""))
                self.assertEqual(app.select_chart_point(event), ("2026-09-22", 72.3, "修改后的日志"))
