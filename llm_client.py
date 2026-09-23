import json

from tools import TOOL_SCHEMAS, execute_tool_json


SYSTEM_PROMPT = """你是用户的个人健康记录分析助手。
你可以通过只读工具查询用户保存的体重和健康随笔。回答问题前，优先使用工具获取事实；可以连续调用多个工具。
回答时说明关键依据的日期或记录，区分记录事实、合理推测和不确定性。不要编造不存在的数据，不做疾病诊断或确定性的医学因果结论。
用户描述严重或紧急的身体、心理问题时，建议及时寻求专业帮助。"""


class HealthAssistant:
    def __init__(self, repository, client, model: str):
        self.repository = repository
        self.client = client
        self.model = model

    def ask(self, messages: list[dict]) -> str:
        conversation = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]
        for _ in range(6):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=conversation,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.2,
            )
            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                return getattr(message, "content", None) or "AI 没有返回文字回答。"
            conversation.append(
                {
                    "role": "assistant",
                    "content": getattr(message, "content", None),
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in tool_calls
                    ],
                }
            )
            for tool_call in tool_calls:
                result = execute_tool_json(
                    self.repository,
                    tool_call.function.name,
                    tool_call.function.arguments,
                )
                conversation.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                )
        return "查询次数超过限制，请把问题缩小到一个时间范围后再试。"
