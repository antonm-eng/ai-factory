"""Structured logs and metrics.

Logs are JSON lines on stdout; in AWS Glue they land in CloudWatch Logs (/aws-glue/python-jobs/output).
Metrics go to CloudWatch under METRICS_NAMESPACE when it is set (AIFactory/ChurnFeatures in Glue).
"""

import json
import os
import sys
from datetime import datetime, timezone

PIPELINE = "churn_features"
NAMESPACE = os.environ.get("METRICS_NAMESPACE")
CODE_VERSION = os.environ.get("CODE_VERSION", "local")


class Telemetry:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self._metrics = []

    def log(self, level: str, message: str, **fields) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": level,
            "message": message,
            "pipeline": PIPELINE,
            "run_id": self.run_id,
            "code_version": CODE_VERSION,
            **fields,
        }
        print(json.dumps(entry), flush=True)

    def metric(self, name: str, value: float, unit: str = "None", **dimensions) -> None:
        dims = [{"Name": "Pipeline", "Value": PIPELINE}] + [{"Name": k, "Value": str(v)} for k, v in dimensions.items()]
        self._metrics.append({"MetricName": name, "Value": value, "Unit": unit, "Dimensions": dims})

    def flush(self) -> None:
        if not NAMESPACE or not self._metrics:
            return
        try:
            import boto3

            boto3.client("cloudwatch").put_metric_data(Namespace=NAMESPACE, MetricData=self._metrics)
        except Exception as exc:  # telemetry must never break the pipeline
            print(f"[observability] metric submit failed: {exc}", file=sys.stderr)
        self._metrics = []
