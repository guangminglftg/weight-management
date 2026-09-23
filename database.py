import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS weight_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date TEXT NOT NULL UNIQUE,
    weight_kg REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS health_journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_weight_date ON weight_records(record_date);
CREATE INDEX IF NOT EXISTS idx_journal_date ON health_journal_entries(entry_date);
"""


def _check_date(value: str) -> str:
    date.fromisoformat(value)
    return value


class HealthRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self):
        with self.connection() as connection:
            connection.executescript(SCHEMA)

    def save_weight(self, record_date: str, weight_kg: float):
        record_date = _check_date(record_date)
        weight_kg = float(weight_kg)
        if not 20 <= weight_kg <= 500:
            raise ValueError("体重应在 20 至 500 kg 之间")
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO weight_records(record_date, weight_kg)
                VALUES (?, ?) ON CONFLICT(record_date) DO UPDATE SET
                weight_kg=excluded.weight_kg, updated_at=CURRENT_TIMESTAMP""",
                (record_date, round(weight_kg, 2)),
            )

    def save_journal(self, entry_date: str, content: str):
        entry_date = _check_date(entry_date)
        content = content.strip()
        with self.connection() as connection:
            if not content:
                connection.execute("DELETE FROM health_journal_entries WHERE entry_date = ?", (entry_date,))
            else:
                connection.execute(
                    """INSERT INTO health_journal_entries(entry_date, content)
                    VALUES (?, ?) ON CONFLICT(entry_date) DO UPDATE SET
                    content=excluded.content, updated_at=CURRENT_TIMESTAMP""",
                    (entry_date, content),
                )

    def get_weights(self, start_date: str | None = None, end_date: str | None = None, limit: int = 500):
        clauses, params = [], []
        if start_date:
            clauses.append("record_date >= ?")
            params.append(_check_date(start_date))
        if end_date:
            clauses.append("record_date <= ?")
            params.append(_check_date(end_date))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT record_date, weight_kg FROM weight_records {where} ORDER BY record_date LIMIT ?",
                (*params, max(1, min(limit, 5000))),
            ).fetchall()
        return [dict(row) for row in rows]

    def search_journals(self, start_date=None, end_date=None, keyword=None, limit=100):
        clauses, params = [], []
        if start_date:
            clauses.append("entry_date >= ?")
            params.append(_check_date(start_date))
        if end_date:
            clauses.append("entry_date <= ?")
            params.append(_check_date(end_date))
        if keyword:
            clauses.append("content LIKE ?")
            params.append(f"%{keyword}%")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT entry_date, content FROM health_journal_entries {where} ORDER BY entry_date LIMIT ?",
                (*params, max(1, min(limit, 1000))),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_daily_record(self, record_date: str):
        record_date = _check_date(record_date)
        weights = self.get_weights(record_date, record_date, 1)
        journals = self.search_journals(record_date, record_date, limit=1)
        return {
            "date": record_date,
            "weight_kg": weights[0]["weight_kg"] if weights else None,
            "journal": journals[0]["content"] if journals else None,
        }

    def summary(self, start_date=None, end_date=None):
        weights = self.get_weights(start_date, end_date)
        journals = self.search_journals(start_date, end_date)
        first = weights[0]["weight_kg"] if weights else None
        latest = weights[-1]["weight_kg"] if weights else None
        return {
            "start_date": start_date,
            "end_date": end_date,
            "weight_record_count": len(weights),
            "journal_entry_count": len(journals),
            "first_weight_kg": first,
            "latest_weight_kg": latest,
            "change_kg": round(latest - first, 2) if first is not None and latest is not None else None,
        }

    def daily_records(self, start_date=None, end_date=None):
        weights = {row["record_date"]: row["weight_kg"] for row in self.get_weights(start_date, end_date)}
        journals = {row["entry_date"]: row["content"] for row in self.search_journals(start_date, end_date)}
        return [
            {"date": key, "weight_kg": weights.get(key), "journal": journals.get(key)}
            for key in sorted(set(weights) | set(journals))
        ]
