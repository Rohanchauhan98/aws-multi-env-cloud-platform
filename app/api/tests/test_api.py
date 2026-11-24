import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

REGION = "ap-southeast-2"


@pytest.fixture
def client(monkeypatch):
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(name, "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)

    with mock_aws():
        boto3.resource("dynamodb", region_name=REGION).create_table(
            TableName="jobs",
            KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "job_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        boto3.client("s3", region_name=REGION).create_bucket(
            Bucket="uploads",
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        from main import app

        yield TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_job_rejects_bad_content_type(client):
    r = client.post("/jobs", json={"filename": "a.exe", "content_type": "application/x-msdownload"})
    assert r.status_code == 415


def test_create_job_returns_upload_form(client):
    r = client.post("/jobs", json={"filename": "cat.png", "content_type": "image/png"})
    assert r.status_code == 201
    body = r.json()
    assert body["job_id"]
    assert body["upload"]["url"]
    assert "key" in body["upload"]["fields"]


def test_get_job_returns_pending_job(client):
    created = client.post("/jobs", json={"filename": "n.txt", "content_type": "text/plain"}).json()
    r = client.get(f"/jobs/{created['job_id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "PENDING"
    assert r.json()["filename"] == "n.txt"


def test_get_unknown_job_is_404(client):
    r = client.get("/jobs/00000000-0000-4000-8000-000000000000")
    assert r.status_code == 404


def test_get_malformed_id_is_400(client):
    r = client.get("/jobs/not-a-uuid")
    assert r.status_code == 400