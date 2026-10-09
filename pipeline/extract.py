"""Step 1: extract recharge events from the daily billing CDC export into the working store.

Billing lands one export per day at raw/recharge_events/dt=<YYYY-MM-DD>/export.csv
(a trailing 30-day snapshot). Source fields are mapped to the contract columns below.
"""

import csv
import io
import sqlite3
from datetime import datetime

from pipeline import storage
from pipeline.contracts import load_contract

# Billing export field -> contract column.
SOURCE_FIELD_MAP = {
    "evt_id": "event_id",
    "subscriber_hash": "msisdn_hash",
    "event_time": "recharge_ts",
    "amount": "amount_azn",
    "sales_chnl_cd": "sales_channel",  # billing v4: chnl_cd renamed
    "plan": "plan_type",
}


def export_key(run_ts: datetime) -> str:
    return f"raw/recharge_events/dt={run_ts:%Y-%m-%d}/export.csv"


def extract(conn: sqlite3.Connection, run_ts: datetime) -> int:
    contract = load_contract("recharge_events")
    columns = [c["name"] for c in contract["columns"]]
    ddl = ", ".join(f'{c["name"]} {c["type"]}' for c in contract["columns"])
    conn.execute("DROP TABLE IF EXISTS recharge_events")
    conn.execute(f"CREATE TABLE recharge_events ({ddl})")

    rows = []
    for record in csv.DictReader(io.StringIO(storage.read_text(export_key(run_ts)))):
        mapped = {SOURCE_FIELD_MAP[k]: v for k, v in record.items() if k in SOURCE_FIELD_MAP}
        rows.append(tuple(mapped[c] for c in columns))

    placeholders = ", ".join("?" for _ in columns)
    conn.executemany(f"INSERT INTO recharge_events ({', '.join(columns)}) VALUES ({placeholders})", rows)
    return len(rows)
