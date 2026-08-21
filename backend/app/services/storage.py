from __future__ import annotations

import logging
from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
        use_ssl=settings.S3_USE_SSL,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def ensure_bucket() -> None:
    client = _client()
    try:
        client.head_bucket(Bucket=settings.S3_BUCKET)
    except ClientError:
        try:
            client.create_bucket(Bucket=settings.S3_BUCKET)
            logger.info("Created S3 bucket %s", settings.S3_BUCKET)
        except ClientError as exc:
            logger.warning("Could not create bucket %s: %s", settings.S3_BUCKET, exc)


def upload_bytes(*, key: str, body: bytes, content_type: str) -> None:
    ensure_bucket()
    _client().put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=body,
        ContentType=content_type,
    )


def delete_object(key: str) -> None:
    try:
        _client().delete_object(Bucket=settings.S3_BUCKET, Key=key)
    except ClientError as exc:
        logger.warning("Failed to delete object %s: %s", key, exc)


def presigned_get_url(key: str, *, expires_in: int = 3600) -> str:
    url = _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires_in,
    )
    # Docker uses minio hostname; browsers need the published localhost URL.
    if settings.S3_PUBLIC_ENDPOINT and settings.S3_ENDPOINT in url:
        url = url.replace(settings.S3_ENDPOINT, settings.S3_PUBLIC_ENDPOINT)
    return url
