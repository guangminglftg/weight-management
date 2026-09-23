import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from database import HealthRepository
from llm_client import HealthAssistant


class FakeCompletions:
    def __init__(self):
        self.calls = []
        self.responses = [
            SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(
                    content=None,
                    tool_calls=[SimpleNamespace(
                        id="call-1",
                        function=SimpleNamespace(name="get_summary", arguments='{"start_date":"2026-09-01"}'),
                    )],
                ))]
            ),
            SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="你最近的记录显示体重有下降趋势。", tool_calls=[]))]
            ),
        ]

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FakeCompletions())


class LlmClientTests(unittest.TestCase):
    def test_assistant_calls_tool_then_answers(self):
        tempdir = tempfile.TemporaryDirectory()
        repository = HealthRepository(Path(tempdir.name) / "health.sqlite3")
        client = FakeClient()
        assistant = HealthAssistant(repository, client, "deepseek-v4-pro")

        answer = assistant.ask([{"role": "user", "content": "我最近怎么样？"}])

        self.assertIn("下降趋势", answer)
        self.assertEqual(len(client.chat.completions.calls), 2)
        self.assertIn("tools", client.chat.completions.calls[0])
        self.assertEqual(client.chat.completions.calls[1]["messages"][-1]["role"], "tool")
        tempdir.cleanup()


if __name__ == "__main__":
    unittest.main()
