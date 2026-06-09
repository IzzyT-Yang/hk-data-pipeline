import json
import argparse
from datetime import datetime, timezone, timedelta
from google.cloud import storage, bigquery
from utils import GCS_BUCKET

BQ_DATASET = "hk_data_pipeline"

WEATHER_SCHEMA = [
    bigquery.SchemaField("time",                   "TIMESTAMP"),
    bigquery.SchemaField("temperature_2m",         "FLOAT64"),
    bigquery.SchemaField("relative_humidity_2m",   "FLOAT64"),
    bigquery.SchemaField("precipitation",          "FLOAT64"),
    bigquery.SchemaField("wind_speed_10m",         "FLOAT64"),
    bigquery.SchemaField("wind_direction_10m",     "FLOAT64"),
    bigquery.SchemaField("weather_code",           "INT64"),
    bigquery.SchemaField("ingested_at",            "TIMESTAMP"),
]

AIR_QUALITY_SCHEMA = [
    bigquery.SchemaField("time",             "TIMESTAMP"),
    bigquery.SchemaField("pm10",             "FLOAT64"),
    bigquery.SchemaField("pm2_5",            "FLOAT64"),
    bigquery.SchemaField("carbon_monoxide",  "FLOAT64"),
    bigquery.SchemaField("nitrogen_dioxide", "FLOAT64"),
    bigquery.SchemaField("sulphur_dioxide",  "FLOAT64"),
    bigquery.SchemaField("ozone",            "FLOAT64"),
    bigquery.SchemaField("european_aqi",     "INT64"),
    bigquery.SchemaField("ingested_at",      "TIMESTAMP"),
]


def columnar_to_rows(data: dict, ingested_at: str) -> list[dict]:
    # Open-Meteo returns arrays keyed by field name; zip them into one dict per hour.
    keys = list(data["hourly"].keys())
    return [
        {k: data["hourly"][k][i] for k in keys} | {"ingested_at": ingested_at}
        for i in range(len(data["hourly"]["time"]))
    ]


def read_gcs_json(bucket_name: str, blob_name: str) -> dict:
    # Downloads and parses a JSON file from GCS.
    client = storage.Client()
    blob = client.bucket(bucket_name).blob(blob_name)
    return json.loads(blob.download_as_text())


def ensure_table(bq: bigquery.Client, table_id: str, schema: list):
    # Creates the BQ table if it doesn't exist; no-ops if it already does.
    try:
        bq.get_table(table_id)
    except Exception:
        table = bigquery.Table(table_id, schema=schema)
        bq.create_table(table)
        print(f"  Created table {table_id}")


def load_to_bq(bq: bigquery.Client, table_id: str, rows: list[dict], schema: list):
    # Appends rows to a BQ table. Re-running the same date will add duplicates; deduplicate in dbt.
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    job = bq.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()


def process_source(source: str, start: str, end: str):
    # Iterates over each day in the date range, reads the corresponding GCS file, and loads it to BQ.
    bq = bigquery.Client()
    ingested_at = datetime.now(timezone.utc).isoformat()

    if source == "weather":
        prefix, table_name, schema = "weather", "weather", WEATHER_SCHEMA
    else:
        prefix, table_name, schema = "air_quality", "air_quality", AIR_QUALITY_SCHEMA

    table_id = f"{bq.project}.{BQ_DATASET}.{table_name}"
    ensure_table(bq, table_id, schema)

    current = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()

    while current <= end_date:
        day_str = str(current)
        blob_name = f"{prefix}/{day_str}.json"
        print(f"  {day_str}...", end=" ", flush=True)

        data = read_gcs_json(GCS_BUCKET, blob_name)
        rows = columnar_to_rows(data, ingested_at)
        load_to_bq(bq, table_id, rows, schema)
        print(f"{len(rows)} rows loaded to {table_id}")

        current += timedelta(days=1)


if __name__ == "__main__":
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(description="Load data from GCS to BigQuery")
    parser.add_argument(
        "--source",
        choices=["weather", "air_quality", "all"],
        default="all",
        help="Which dataset to load (default: all)",
    )
    parser.add_argument("--start-date", default=today, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=today, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    sources = ["weather", "air_quality"] if args.source == "all" else [args.source]

    for source in sources:
        print(f"Loading {source}: {args.start_date} → {args.end_date}")
        process_source(source, args.start_date, args.end_date)
