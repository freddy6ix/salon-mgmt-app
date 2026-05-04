import asyncio

from google.cloud import storage


async def deliver(content: str, bucket_name: str, object_name: str) -> str:
    """Upload briefing content to GCS. Returns the gs:// URI."""
    await asyncio.to_thread(_upload, content, bucket_name, object_name)
    return f"gs://{bucket_name}/{object_name}"


def _upload(content: str, bucket_name: str, object_name: str) -> None:
    client = storage.Client()
    blob = client.bucket(bucket_name).blob(object_name)
    blob.upload_from_string(content, content_type="text/markdown; charset=utf-8")
