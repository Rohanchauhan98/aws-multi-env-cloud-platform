import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
TABLE_NAME = os.environ.get("TABLE_NAME", "jobs")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "uploads")

ALLOWED_TYPES = {"image/png", "image/jpeg", "text/plain", "application/pdf"}
MAX_BYTES = 5 * 1024 * 1024
UPLOAD_TTL_SECONDS = 300

app = FastAPI(title="File Pipeline API")


def _table():
    return boto3.resource("dynamodb", region_name=REGION).Table(TABLE_NAME)


def _s3():
    return boto3.client(
        "s3",
        region_name=REGION,
        endpoint_url=f"https://s3.{REGION}.amazonaws.com",
        config=Config(signature_version="s3v4"),
    )


class JobRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=200)
    content_type: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/jobs", status_code=201)
def create_job(req: JobRequest):
    if req.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported content type")

    job_id = str(uuid.uuid4())
    key = f"uploads/{job_id}"

    _table().put_item(
        Item={
            "job_id": job_id,
            "status": "PENDING",
            "filename": req.filename,
            "content_type": req.content_type,
            "s3_key": key,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    upload = _s3().generate_presigned_post(
        Bucket=BUCKET_NAME,
        Key=key,
        Fields={"Content-Type": req.content_type},
        Conditions=[
            {"Content-Type": req.content_type},
            ["content-length-range", 1, MAX_BYTES],
        ],
        ExpiresIn=UPLOAD_TTL_SECONDS,
    )
    return {"job_id": job_id, "upload": upload}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job id")

    item = _table().get_item(Key={"job_id": job_id}).get("Item")
    if item is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return item