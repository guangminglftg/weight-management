from datetime import date, timedelta

import pandas as pd
from html import escape


def date_range(start_date: str, end_date: str):
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("结束日期不能早于开始日期")
    return [(start + timedelta(days=index)).isoformat() for index in range((end - start).days + 1)]


def build_weight_data(records: list[dict]) -> pd.DataFrame:
    points = [
        {"date": row["date"], "weight_kg": float(row["weight_kg"])}
        for row in records
        if row.get("weight_kg") is not None
    ]
    return pd.DataFrame(points, columns=["date", "weight_kg"])


def build_clickable_chart(records):
    points = build_weight_data(records).to_dict("records")
    if not points:
        return '<div class="empty-chart">这个时间范围还没有体重记录。</div>'
    values = [row["weight_kg"] for row in points]
    lower = min(values) - 0.5
    span = max(values) - lower + 0.5
    first = date.fromisoformat(points[0]["date"])
    days = max((date.fromisoformat(points[-1]["date"]) - first).days, 1)
    coordinates = []
    markers = []
    for row in points:
        selected_date = escape(row["date"])
        horizontal = 360 if len(points) == 1 else 55 + (date.fromisoformat(row["date"]) - first).days / days * 610
        vertical = 220 - (row["weight_kg"] - lower) / span * 180
        coordinates.append(f"{horizontal},{vertical}")
        label = f'{selected_date} · {row["weight_kg"]:.2f} kg'
        markers.append(f'<g role="button" tabindex="0" data-date="{selected_date}" aria-label="查看 {label}" style="cursor:pointer"><title>{label}，点击查看和修改</title><circle cx="{horizontal}" cy="{vertical}" r="15" fill="transparent"/><circle cx="{horizontal}" cy="{vertical}" r="6" fill="white" stroke="#007aff" stroke-width="3"/><text x="{horizontal}" y="{vertical - 20}" text-anchor="middle" fill="#515154" font-size="12">{row["weight_kg"]:.2f}</text></g>')
    return f'<div class="chart-shell"><svg viewBox="0 0 720 260" aria-label="体重趋势"><path d="M40 80H680 M40 140H680 M40 200H680" stroke="#e5e5ea"/><polyline points="{" ".join(coordinates)}" fill="none" stroke="#007aff" stroke-width="3"/>{"".join(markers)}</svg><div class="chart-labels"><span>{escape(points[0]["date"])}</span><span>{escape(points[-1]["date"])}</span></div></div>'
