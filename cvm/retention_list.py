"""Daily CVM retention list (owner: CVM, scoring: Data Science). Runs as Glue job cvm_retention_list_daily at 06:00 UTC.

Scores the latest published churn_features snapshot with the approved model and publishes the top 10%
to campaigns/retention_list/dt=<date>/retention_list.csv (Athena: ai_factory.retention_list).
The manifest under campaigns/_lists/ records which features snapshot the list was built from and how
much of the list changed since the previous day.
"""

import csv
import io
import json
import os
from datetime import datetime, timedelta, timezone

from cvm.scoring import LIST_SHARE, MODEL, churn_score
from pipeline import storage

CODE_VERSION = os.environ.get("CODE_VERSION", "local")


def _latest_snapshot(as_of: datetime) -> dict:
    """Newest successful churn_features run published at or before as_of (searching 7 days back)."""
    best = None
    for back in range(8):
        day = (as_of - timedelta(days=back)).strftime("%Y-%m-%d")
        for key in storage.list_keys(f"features/_runs/dt={day}/"):
            manifest = json.loads(storage.read_text(key))
            published = datetime.fromisoformat(manifest["published_at"])
            if published <= as_of and (best is None or published > best["_published"]):
                best = {**manifest, "_published": published, "_dt": day}
        if best:
            return best
    raise RuntimeError("no churn_features snapshot published in the last 7 days")


def _read_list(day: str) -> list:
    key = f"campaigns/retention_list/dt={day}/retention_list.csv"
    if not storage.exists(key):
        return []
    return list(csv.DictReader(io.StringIO(storage.read_text(key))))


def run() -> dict:
    now = datetime.now(timezone.utc)
    if os.environ.get("RUN_DATE"):  # backfill: build that day's list as of 06:00 UTC
        now = datetime.strptime(os.environ["RUN_DATE"], "%Y-%m-%d").replace(hour=6, tzinfo=timezone.utc)
    list_date = now.strftime("%Y-%m-%d")

    snapshot = _latest_snapshot(now)
    features = list(csv.DictReader(io.StringIO(
        storage.read_text(f"features/churn_features/dt={snapshot['_dt']}/churn_features.csv"))))
    scored = sorted(
        ({**row, "churn_score": round(churn_score(row), 4)} for row in features),
        key=lambda r: r["churn_score"], reverse=True,
    )
    top = scored[: max(1, int(len(scored) * LIST_SHARE))]

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["msisdn_hash", "list_rank", "churn_score", "recharge_cnt_30d", "avg_recharge_30d", "days_since_last_recharge"])
    for rank, row in enumerate(top, start=1):
        writer.writerow([row["msisdn_hash"], rank, row["churn_score"], row["recharge_cnt_30d"],
                         row["avg_recharge_30d"], row["days_since_last_recharge"]])
    storage.write_text(f"campaigns/retention_list/dt={list_date}/retention_list.csv", out.getvalue())

    previous_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    previous = {r["msisdn_hash"] for r in _read_list(previous_date)}
    current = {r["msisdn_hash"] for r in top}
    changed = round(100.0 * len(current - previous) / len(current), 1) if previous else None

    # The snapshot holds billing data up to its export cut-off: 00:00 UTC of the snapshot date.
    data_through = datetime.strptime(snapshot["_dt"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    manifest = {
        "list_date": list_date,
        "list_run_id": os.environ.get("GLUE_JOB_RUN_ID") or f"local_{now:%Y%m%dT%H%M}",
        "built_at": now.isoformat(timespec="seconds"),
        "model": MODEL,
        "features_run_id": snapshot["run_id"],
        "features_published_at": snapshot["published_at"],
        "features_data_through": data_through.isoformat(timespec="seconds"),
        "data_age_hours": round((now - data_through).total_seconds() / 3600, 1),
        "scored_subscribers": len(scored),
        "list_size": len(top),
        "previous_list_date": previous_date if previous else None,
        "changed_vs_previous_pct": changed,
        "code_version": CODE_VERSION,
    }
    storage.write_text(f"campaigns/_lists/dt={list_date}/manifest.json", json.dumps(manifest, indent=2))
    print(json.dumps({"level": "info", "message": "retention list published", **manifest}), flush=True)
    return manifest


if __name__ == "__main__":
    run()
