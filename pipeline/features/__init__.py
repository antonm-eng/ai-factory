"""Step 3: build churn features from the validated batch."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

FEATURES_DIR = Path(__file__).parent
FEATURE_SETS = ["recharge", "usage"]


def build_features(conn: sqlite3.Connection, run_ts: datetime) -> dict:
    # Features are as of the export cut-off (00:00 UTC of the run date), so every run of a day publishes the same snapshot.
    as_of = run_ts.replace(hour=0, minute=0, second=0, microsecond=0)
    params = {
        "as_of": as_of.strftime("%Y-%m-%d %H:%M:%S"),
        "window_start": (as_of - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
    }
    counts = {}
    for name in FEATURE_SETS:
        sql = (FEATURES_DIR / f"{name}.sql").read_text()
        conn.execute(f"DROP TABLE IF EXISTS features_{name}")
        conn.execute(f"CREATE TABLE features_{name} AS {sql}", params)
        counts[name] = conn.execute(f"SELECT COUNT(*) FROM features_{name}").fetchone()[0]
    return counts
