"""Run the churn feature pipeline end to end: extract -> validate -> build_features -> publish.

In AWS this runs as the Glue job churn_features_daily (every 30 minutes, see glue/run_job.py).
Locally: DATA_BUCKET unset reads and writes under ./data.
"""

import os
import sqlite3
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone

from pipeline.extract import extract
from pipeline.features import build_features
from pipeline.observability import CODE_VERSION, Telemetry
from pipeline.publish import publish
from pipeline.validate import validate

STEPS = ["extract", "validate", "build_features", "publish"]


class PipelineFailed(Exception):
    pass


def run() -> dict:
    run_ts = datetime.now(timezone.utc).replace(tzinfo=None)
    if os.environ.get("RUN_DATE"):  # backfill: process that day's export as of 02:00 UTC
        run_ts = datetime.strptime(os.environ["RUN_DATE"], "%Y-%m-%d").replace(hour=2)
    run_id = os.environ.get("GLUE_JOB_RUN_ID") or f"churn_features_{run_ts:%Y%m%dT%H%M}_{uuid.uuid4().hex[:6]}"
    t = Telemetry(run_id)
    conn = sqlite3.connect(":memory:")
    t.log("info", "pipeline run started", run_ts=run_ts.isoformat())

    actions = {
        "extract": lambda: {"rows": extract(conn, run_ts)},
        "validate": lambda: validate(conn),
        "build_features": lambda: build_features(conn, run_ts),
        "publish": lambda: {"rows_written": publish(conn, run_ts, run_id, CODE_VERSION)},
    }
    started = time.monotonic()
    for n, step in enumerate(STEPS, start=1):
        step_started = time.monotonic()
        try:
            result = actions[step]()
        except Exception as exc:
            message = f"step {n}/{len(STEPS)} {step} failed: {type(exc).__name__}: {exc}"
            t.log("error", message, step=step, step_index=n,
                  error={"kind": type(exc).__name__, "message": str(exc), "stack": traceback.format_exc()})
            t.log("error", "pipeline run failed; churn_features not refreshed, training and scoring keep the previous snapshot")
            t.metric("RunSuccess", 0)
            t.metric("RowsWritten", 0, "Count")
            t.metric("StepFailed", 1, "Count", Step=step)
            t.flush()
            raise PipelineFailed(message) from exc
        t.metric("StepDurationSeconds", round(time.monotonic() - step_started, 3), "Seconds", Step=step)
        t.log("info", f"step {n}/{len(STEPS)} {step} succeeded", step=step, step_index=n, result=result)

    rows = result["rows_written"]
    t.metric("RunSuccess", 1)
    t.metric("RowsWritten", rows, "Count")
    t.metric("RunDurationSeconds", round(time.monotonic() - started, 3), "Seconds")
    t.log("info", "pipeline run succeeded; churn_features refreshed", rows_written=rows)
    t.flush()
    return {"run_id": run_id, "rows_written": rows}


def main() -> int:
    try:
        run()
    except PipelineFailed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
