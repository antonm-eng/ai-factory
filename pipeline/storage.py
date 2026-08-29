"""Where the pipeline reads and writes: S3 when running in AWS Glue, a local folder in CI and on laptops."""

import os
from pathlib import Path

BUCKET = os.environ.get("DATA_BUCKET")
LOCAL_ROOT = Path(os.environ.get("LOCAL_DATA_ROOT", "data"))


def _s3():
    import boto3

    return boto3.client("s3")


def read_text(key: str) -> str:
    if BUCKET:
        return _s3().get_object(Bucket=BUCKET, Key=key)["Body"].read().decode()
    return (LOCAL_ROOT / key).read_text()


def write_text(key: str, body: str) -> None:
    if BUCKET:
        _s3().put_object(Bucket=BUCKET, Key=key, Body=body.encode())
        return
    path = LOCAL_ROOT / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def list_keys(prefix: str) -> list:
    if BUCKET:
        keys, token = [], None
        while True:
            kwargs = {"Bucket": BUCKET, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            page = _s3().list_objects_v2(**kwargs)
            keys += [o["Key"] for o in page.get("Contents", [])]
            if not page.get("IsTruncated"):
                return keys
            token = page["NextContinuationToken"]
    root = LOCAL_ROOT / prefix
    base = root if root.is_dir() else root.parent
    return sorted(str(p.relative_to(LOCAL_ROOT)) for p in base.rglob("*") if p.is_file() and str(p.relative_to(LOCAL_ROOT)).startswith(prefix))


def exists(key: str) -> bool:
    try:
        read_text(key)
        return True
    except Exception:
        return False

