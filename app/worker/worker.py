import hashlib
import io
import json
import logging
import os
import signal
import uuid
from datetime import datetime, timezone
from urllib.parse import unquote_plus

import boto3
from PIL import Image

REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
TABLE_NAME = os.environ.get("TABLE_NAME", "jobs")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "uploads")
QUEUE_URL = os.environ.get("QUEUE_URL", "")
MAX_RECEIVES = int(os.environ.get("MAX_RECEIVES", "3"))

THUMB_SIZE = (128, 128)
IMAGE_FORMATS = {"image/png": "PNG", "image/jpeg": "JPEG"}

# Reject decompression bombs: larger images raise an error instead of using all memory.
Image.MAX_IMAGE_PIXELS = 25_000_000

log = logging.getLogger("worker")
_stop = False


def _table():
    return boto3.resource("dynamodb", region_name=REGION).Table(TABLE_NAME)


def _s3():
    return boto3.client("s3", region_name=REGION)


def _sqs():
    return boto3.client("sqs", region_name=REGION)


class JobError(Exception):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat()


def keys_from_body(body):
    data = json.loads(body)
    if data.get("Event") == "s3:TestEvent":
        return []
    return [unquote_plus(r["s3"]["object"]["key"]) for r in data.get("Records", [])]


def _job_id_from_key(key):
    job_id = key.rsplit("/", 1)[-1]
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise JobError(f"unexpected object key {key!r}")
    return job_id


def _mark(job_id, status, extra):
    names = {"#s": "status"}
    values = {":s": status, ":t": _now()}
    sets = ["#s = :s", "updated_at = :t"]
    for i, (name, value) in enumerate(extra.items()):
        names[f"#k{i}"] = name
        values[f":v{i}"] = value
        sets.append(f"#k{i} = :v{i}")
    _table().update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET " + ", ".join(sets),
        ConditionExpression="attribute_exists(job_id)",
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def process_key(key):
    job_id = _job_id_from_key(key)
    job = _table().get_item(Key={"job_id": job_id}).get("Item")
    if job is None:
        raise JobError(f"no job record for {job_id}")
    if job.get("status") == "DONE":
        return

    data = _s3().get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
    result = {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}

    fmt = IMAGE_FORMATS.get(job.get("content_type"))
    if fmt:
        thumb_key = f"thumbnails/{job_id}"
        with Image.open(io.BytesIO(data)) as img:
            img.thumbnail(THUMB_SIZE)
            buf = io.BytesIO()
            img.save(buf, format=fmt)
        _s3().put_object(
            Bucket=BUCKET_NAME,
            Key=thumb_key,
            Body=buf.getvalue(),
            ContentType=job["content_type"],
        )
        result["thumbnail_key"] = thumb_key

    _mark(job_id, "DONE", result)


def _fail(msg, exc):
    try:
        for key in keys_from_body(msg["Body"]):
            _mark(_job_id_from_key(key), "FAILED", {"error": str(exc)[:200]})
    except Exception:
        log.exception("could not mark job as failed")


def handle_message(msg):
    """Return True if the message should be deleted from the queue."""
    receives = int(msg.get("Attributes", {}).get("ApproximateReceiveCount", "1"))
    try:
        for key in keys_from_body(msg["Body"]):
            process_key(key)
        return True
    except Exception as exc:
        log.exception("processing failed (receive %s of %s)", receives, MAX_RECEIVES)
        if receives >= MAX_RECEIVES:
            _fail(msg, exc)
        return False


def poll_once(wait=20):
    resp = _sqs().receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=5,
        WaitTimeSeconds=wait,
        AttributeNames=["ApproximateReceiveCount"],
    )
    messages = resp.get("Messages", [])
    for m in messages:
        if handle_message(m):
            _sqs().delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=m["ReceiptHandle"])
    return len(messages)


def _request_stop(signum, frame):
    global _stop
    _stop = True


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    log.info("worker started")
    while not _stop:
        poll_once()
    log.info("worker stopped")


if __name__ == "__main__":
    main()