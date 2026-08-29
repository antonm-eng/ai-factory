"""Step 4: publish the joined feature table consumed by churn training and scoring.

Writes features/churn_features/dt=<YYYY-MM-DD>/churn_features.csv (Athena: ai_factory.churn_features)
and a run manifest under features/_runs/ that training jobs record as their snapshot.
"""

import csv
import io
import json
import os
import sqlite3
from datetime import datetime, timezone

from pipeline import storage

MIN_ROWS = 1000


class PublishCheckFailed(Exception):
    pass


def publish(conn: sqlite3.Connection, run_ts: datetime, run_id: str, code_version: str) -> int:
    rows = conn.execute(
        """
        SELECT r.*, u.days_since_last_recharge, u.min_recharge_30d, u.max_recharge_30d
        FROM features_recharge r JOIN features_usage u USING (msisdn_hash)
        """
    )
    header = [d[0] for d in rows.description]
    data = rows.fetchall()
    if len(data) < MIN_ROWS:
        raise PublishCheckFailed(f"only {len(data)} rows in churn_features, expected >= {MIN_ROWS}")

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(header)
    writer.writerows(data)
    storage.write_text(f"features/churn_features/dt={run_ts:%Y-%m-%d}/churn_features.csv", out.getvalue())

    manifest = {
        "run_id": run_id,
        "code_version": code_version,
        "rows": len(data),
        "columns": header,
        "published_at": (run_ts.replace(tzinfo=timezone.utc) if os.environ.get("RUN_DATE") else datetime.now(timezone.utc)).isoformat(timespec="seconds"),
    }
    storage.write_text(f"features/_runs/dt={run_ts:%Y-%m-%d}/{run_id}.json", json.dumps(manifest, indent=2))
    return len(data)
