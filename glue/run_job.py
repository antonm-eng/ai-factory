"""AWS Glue (Python shell) entry point for the churn_features_daily job.

Loads the released pipeline package (s3://<DATA_BUCKET>/code/pipeline.zip, published on every
merge to main) and runs it. A failed step raises, so the Glue job run ends FAILED with the step's error.
"""

import io
import os
import sys
import zipfile

import boto3


def _arg(name, default=""):
    flag = f"--{name}"
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def _current_run_id(job_name):
    # The job allows one concurrent run, so the RUNNING run is this one. Logs and manifests use its id.
    try:
        runs = boto3.client("glue").get_job_runs(JobName=job_name, MaxResults=5)["JobRuns"]
        return next((r["Id"] for r in runs if r["JobRunState"] == "RUNNING"), "")
    except Exception:
        return ""


bucket = _arg("DATA_BUCKET")
os.environ["DATA_BUCKET"] = bucket
os.environ["METRICS_NAMESPACE"] = _arg("METRICS_NAMESPACE", "AIFactory/ChurnFeatures")
os.environ["GLUE_JOB_RUN_ID"] = _arg("JOB_RUN_ID") or _current_run_id(_arg("JOB_NAME", "churn_features_daily"))
if _arg("RUN_DATE"):  # backfill a past day's snapshot
    os.environ["RUN_DATE"] = _arg("RUN_DATE")

package = boto3.client("s3").get_object(Bucket=bucket, Key="code/pipeline.zip")["Body"].read()
zipfile.ZipFile(io.BytesIO(package)).extractall("/tmp/ai-factory")
with open("/tmp/ai-factory/VERSION") as f:
    os.environ["CODE_VERSION"] = f.read().strip()
sys.path.insert(0, "/tmp/ai-factory")

from pipeline.run import run  # noqa: E402

run()
