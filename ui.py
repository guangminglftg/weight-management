from datetime import date, timedelta
from html import escape



def default_dates():
    today = date.today()
    return (today - timedelta(days=6)).isoformat(), today.isoformat()


def parse_weight(value):
    if value in (None, ""):
        return None
    weight = float(value)
    if not 20 <= weight <= 500:
        raise ValueError("体重应在 20 至 500 kg 之间")
    return round(weight, 2)


def load_form_values(repository, record_date: str):
    record = repository.get_daily_record(record_date)
    return record["weight_kg"], record["journal"] or ""


def point_date_from_records(records: list[dict], point_index):
    points = [row for row in records if row.get("weight_kg") is not None]
    if isinstance(point_index, (list, tuple)):
        point_index = point_index[-1] if point_index else None
    if not isinstance(point_index, int) or not 0 <= point_index < len(points):
        return None
    return points[point_index]["date"]


def journal_cards(records: list[dict]) -> str:
    if not records:
        return '<div class="empty-journal">还没有健康随笔。</div>'
    cards = []
    for row in reversed(records[-30:]):
        content = row.get("journal")
        if not content:
            continue
        weight = f' · {row["weight_kg"]:.2f} kg' if row.get("weight_kg") is not None else ""
        cards.append(
            f'<article class="journal-card"><div class="journal-date">{escape(row["date"])}{weight}</div>'
            f'<div class="journal-content">{escape(content).replace(chr(10), "<br>")}</div></article>'
        )
    return "".join(cards) or '<div class="empty-journal">还没有健康随笔。</div>'


def summary_text(summary: dict) -> str:
    change = summary.get("change_kg")
    change_text = "暂无变化数据" if change is None else f"变化 {change:+.2f} kg"
    return f"记录 {summary.get('weight_record_count', 0)} 天 · {change_text} · 随笔 {summary.get('journal_entry_count', 0)} 篇"
