import json
import os
from google.cloud import storage
from google.oauth2 import service_account

GCS_BUCKET = "hk-data-pipeline"
LATITUDE = 22.3193
LONGITUDE = 114.1694
TIMEZONE = "Asia/Hong_Kong"


def get_credentials():
    # reads service account JSON from env var — accepts raw JSON or base64-encoded JSON
    key_val = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if key_val:
        import base64
        key_val = key_val.strip()
        try:
            info = json.loads(key_val)  # try raw JSON first
        except json.JSONDecodeError:
            key_json = base64.b64decode(key_val + "==").decode("utf-8")
            info = json.loads(key_json)
        return service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    return None  # falls back to ADC (local dev / VM service account)


def upload_to_gcs(data, bucket_name: str, blob_name: str) -> str:
    client = storage.Client(credentials=get_credentials())
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    return f"gs://{bucket_name}/{blob_name}"
