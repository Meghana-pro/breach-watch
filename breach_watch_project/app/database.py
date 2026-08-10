import json
import os
import sqlite3
from pathlib import Path
from datetime import date

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "breach_watch.db"
DB_PATH = Path(os.getenv("BREACH_WATCH_DB_PATH", str(DEFAULT_DB))).resolve()


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL DEFAULT '',
                incident_date TEXT NOT NULL,
                data_types_json TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                risk_reasons_json TEXT NOT NULL,
                action_completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        count = con.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        if count == 0:
            samples = [
                {
                    "organization": "Example Market",
                    "title": "Demo: customer email exposure",
                    "description": "Demonstration record only. Report says email addresses and usernames may have been exposed.",
                    "source_name": "Local demo dataset",
                    "source_url": "",
                    "incident_date": str(date.today()),
                    "data_types": ["email_addresses", "usernames"],
                },
                {
                    "organization": "Sample Finance Service",
                    "title": "Demo: suspected credential exposure",
                    "description": "Demonstration record only. The sample description mentions passwords and access tokens.",
                    "source_name": "Local demo dataset",
                    "source_url": "",
                    "incident_date": str(date.today()),
                    "data_types": ["passwords", "authentication_tokens", "financial_data"],
                },
                {
                    "organization": "Training Health Portal",
                    "title": "Demo: personal information incident",
                    "description": "Demonstration record only. Sample data is not a real breach report.",
                    "source_name": "Local demo dataset",
                    "source_url": "",
                    "incident_date": str(date.today()),
                    "data_types": ["personal_information", "health_data"],
                },
            ]
            from app.risk import score_incident
            for item in samples:
                risk = score_incident(item["data_types"], item["description"])
                con.execute("""
                    INSERT INTO incidents
                    (organization, title, description, source_name, source_url, incident_date,
                     data_types_json, risk_score, risk_level, risk_reasons_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item["organization"], item["title"], item["description"], item["source_name"],
                    item["source_url"], item["incident_date"], json.dumps(item["data_types"]),
                    risk["risk_score"], risk["risk_level"], json.dumps(risk["risk_reasons"])
                ))


def row_to_dict(row):
    item = dict(row)
    item["data_types"] = json.loads(item.pop("data_types_json"))
    item["risk_reasons"] = json.loads(item.pop("risk_reasons_json"))
    item["action_completed"] = bool(item["action_completed"])
    return item


def list_incidents():
    with connect() as con:
        rows = con.execute("SELECT * FROM incidents ORDER BY id DESC").fetchall()
    return [row_to_dict(row) for row in rows]


def get_incident(incident_id: int):
    with connect() as con:
        row = con.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    return row_to_dict(row) if row else None


def create_incident(item: dict, risk: dict):
    with connect() as con:
        cursor = con.execute("""
            INSERT INTO incidents
            (organization, title, description, source_name, source_url, incident_date,
             data_types_json, risk_score, risk_level, risk_reasons_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["organization"], item["title"], item["description"], item["source_name"],
            item.get("source_url", ""), item["incident_date"], json.dumps(item["data_types"]),
            risk["risk_score"], risk["risk_level"], json.dumps(risk["risk_reasons"])
        ))
        new_id = cursor.lastrowid
    return get_incident(new_id)


def set_action_completed(incident_id: int, completed: bool):
    with connect() as con:
        cursor = con.execute(
            "UPDATE incidents SET action_completed = ? WHERE id = ?",
            (1 if completed else 0, incident_id)
        )
        if cursor.rowcount == 0:
            return None
    return get_incident(incident_id)


def summary():
    with connect() as con:
        rows = con.execute("SELECT risk_level, COUNT(*) AS total FROM incidents GROUP BY risk_level").fetchall()
        total = con.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        completed = con.execute("SELECT COUNT(*) FROM incidents WHERE action_completed = 1").fetchone()[0]
    counts = {"Low": 0, "Medium": 0, "High": 0}
    for row in rows:
        counts[row["risk_level"]] = row["total"]
    return {
        "total_incidents": total,
        "high_risk": counts["High"],
        "medium_risk": counts["Medium"],
        "low_risk": counts["Low"],
        "actions_completed": completed,
    }
