import json
from google.cloud import storage

GCS_BUCKET = "hk-data-pipeline"
LATITUDE = 22.3193
LONGITUDE = 114.1694
TIMEZONE = "Asia/Hong_Kong"


def upload_to_gcs(data, bucket_name: str, blob_name: str) -> str:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    return f"gs://{bucket_name}/{blob_name}"
