import hashlib
import io
import json

import boto3
import pytest
from moto import mock_aws
from PIL import Image

REGION = "ap-southeast-2"
JOB_ID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture
def env(monkeypatch):
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(name, "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)

    with mock_aws():
        table = boto3.resource("dynamodb", region_name=REGION).create_table(
            TableName="jobs",
            KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "job_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(
            Bucket="uploads",
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        sqs = boto3.client("sqs", region_name=REGION)
        queue_url = sqs.create_queue(QueueName="jobs-queue")["QueueUrl"]

        import worker

        monkeypatch.setattr(worker, "QUEUE_URL", queue_url)
        yield {"worker": worker, "table": table, "s3": s3, "sqs": sqs, "queue_url": queue_url}


def add_job(env, content_type, body, status="PENDING"):
    key = f"uploads/{JOB_ID}"
    env["table"].put_item(
        Item={"job_id": JOB_ID, "status": status, "content_type": content_type, "s3_key": key}
    )
    env["s3"].put_object(Bucket="uploads", Key=key, Body=body)
    return key


def s3_event(key, receives="1"):
    body = json.dumps({"Records": [{"s3": {"bucket": {"name": "uploads"}, "object": {"key": key}}}]})
    return {"Body": body, "Attributes": {"ApproximateReceiveCount": receives}}


def png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (400, 300), "red").save(buf, format="PNG")
    return buf.getvalue()


def get_job(env):
    return env["table"].get_item(Key={"job_id": JOB_ID})["Item"]


def test_image_job_done_with_thumbnail(env):
    data = png_bytes()
    key = add_job(env, "image/png", data)

    assert env["worker"].handle_message(s3_event(key)) is True

    job = get_job(env)
    assert job["status"] == "DONE"
    assert job["sha256"] == hashlib.sha256(data).hexdigest()
    assert job["size_bytes"] == len(data)
    thumb = env["s3"].get_object(Bucket="uploads", Key=job["thumbnail_key"])["Body"].read()
    with Image.open(io.BytesIO(thumb)) as t:
        assert max(t.size) <= 128


def test_text_job_done_without_thumbnail(env):
    data = b"hello pipeline"
    key = add_job(env, "text/plain", data)

    assert env["worker"].handle_message(s3_event(key)) is True

    job = get_job(env)
    assert job["status"] == "DONE"
    assert job["sha256"] == hashlib.sha256(data).hexdigest()
    assert "thumbnail_key" not in job


def test_already_done_job_is_skipped(env):
    key = add_job(env, "text/plain", b"new content", status="DONE")
    env["table"].update_item(
        Key={"job_id": JOB_ID},
        UpdateExpression="SET sha256 = :s",
        ExpressionAttributeValues={":s": "original"},
    )

    assert env["worker"].handle_message(s3_event(key)) is True
    assert get_job(env)["sha256"] == "original"


def test_missing_job_is_not_deleted(env):
    key = f"uploads/{JOB_ID}"
    assert env["worker"].handle_message(s3_event(key)) is False


def test_third_failed_receive_marks_job_failed(env):
    key = add_job(env, "image/png", b"this is not an image")

    assert env["worker"].handle_message(s3_event(key, receives="1")) is False
    assert get_job(env)["status"] == "PENDING"

    assert env["worker"].handle_message(s3_event(key, receives="3")) is False
    job = get_job(env)
    assert job["status"] == "FAILED"
    assert "error" in job


def test_s3_test_event_is_deleted(env):
    msg = {"Body": json.dumps({"Event": "s3:TestEvent"})}
    assert env["worker"].handle_message(msg) is True


def test_poll_once_end_to_end(env):
    key = add_job(env, "text/plain", b"queued work")
    env["sqs"].send_message(QueueUrl=env["queue_url"], MessageBody=s3_event(key)["Body"])

    assert env["worker"].poll_once(wait=0) == 1
    assert get_job(env)["status"] == "DONE"