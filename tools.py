import json
from datetime import date

from database import HealthRepository


MAX_RESULTS = 100


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_health_journals",
            "description": "按日期范围或关键词搜索用户的健康随笔，内容可能包含饮食、心理、睡眠、运动和身体感受。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD，可省略"},
                    "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD，可省略"},
                    "keyword": {"type": "string", "description": "日志内容关键词，可省略"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weight_records",
            "description": "查询用户指定时间范围内的体重记录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD，可省略"},
                    "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD，可省略"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_health_record",
            "description": "查询某一天的体重和健康随笔。",
            "parameters": {
                "type": "object",
                "required": ["date"],
                "properties": {"date": {"type": "string", "description": "日期 YYYY-MM-DD"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_summary",
            "description": "获取指定时间范围的体重起止值、变化幅度、记录天数和随笔数量。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD，可省略"},
                    "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD，可省略"},
                },
            },
        },
    },
]


def _date_or_today(value):
    if value:
        date.fromisoformat(value)
        return value
    return None


def execute_tool(repository: HealthRepository, name: str, arguments: dict):
    try:
        if name == "search_health_journals":
            rows = repository.search_journals(
                _date_or_today(arguments.get("start_date")),
                _date_or_today(arguments.get("end_date")),
                (arguments.get("keyword") or "").strip() or None,
                MAX_RESULTS,
            )
            return {"records": rows, "count": len(rows)}
        if name == "get_weight_records":
            rows = repository.get_weights(
                _date_or_today(arguments.get("start_date")),
                _date_or_today(arguments.get("end_date")),
                MAX_RESULTS,
            )
            return {"records": rows, "count": len(rows)}
        if name == "get_daily_health_record":
            return repository.get_daily_record(_date_or_today(arguments.get("date")))
        if name == "get_summary":
            return repository.summary(
                _date_or_today(arguments.get("start_date")),
                _date_or_today(arguments.get("end_date")),
            )
        return {"error": f"未知工具: {name}"}
    except (ValueError, TypeError) as error:
        return {"error": str(error)}


def execute_tool_json(repository: HealthRepository, name: str, arguments_json: str) -> str:
    try:
        arguments = json.loads(arguments_json or "{}")
    except json.JSONDecodeError:
        return json.dumps({"error": "工具参数不是有效 JSON"}, ensure_ascii=False)
    return json.dumps(execute_tool(repository, name, arguments), ensure_ascii=False)
