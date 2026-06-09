import json
import re
import argparse
import requests
from datetime import datetime, timezone, timedelta
from utils import GCS_BUCKET, LATITUDE, LONGITUDE, TIMEZONE, upload_to_gcs

# Live AQHI source (past 24h only, official EPD station readings)
AQHI_URL = "https://www.aqhi.gov.hk/js/data/past_24_pollutant.js"
AQHI_DATA_TYPES = {
    "aqhi":   "station_24_data",       # AQHI + all pollutants (hourly)
    "8hour":  "station_data_8_hours",  # rolling 8-hour ozone
    "24hour": "station_data_24_hours", # rolling 24-hour PM
}

# Historical source (Open-Meteo, model-based, supports date ranges)
OPENMETEO_AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPENMETEO_VARS = "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,european_aqi"


def fetch_live_aqhi(data_type: str = "aqhi") -> list[dict]:
    js_var = AQHI_DATA_TYPES[data_type]
    response = requests.get(AQHI_URL)
    response.raise_for_status()

    match = re.search(rf"var {js_var}\s*=\s*(\[.*?\]);(?:\s*var |\Z)", response.text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find {js_var} in response")

    raw = json.loads(match.group(1))
    return [record for station in raw for record in station]


def fetch_historical(start_date: str, end_date: str) -> dict:
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": OPENMETEO_VARS,
        "timezone": TIMEZONE,
        "start_date": start_date,
        "end_date": end_date,
    }
    response = requests.get(OPENMETEO_AQ_URL, params=params)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(description="Fetch HK air quality data")
    parser.add_argument("--start-date", help="Start date for historical fetch (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date for historical fetch (YYYY-MM-DD)")
    parser.add_argument(
        "--data-type",
        choices=list(AQHI_DATA_TYPES.keys()),
        default="aqhi",
        help="Live AQHI dataset: aqhi (default), 8hour, 24hour. Ignored when using --start-date/--end-date.",
    )
    parser.add_argument("--no-upload", action="store_true", help="Skip GCS upload")
    args = parser.parse_args()

    if args.start_date or args.end_date:
        start = args.start_date or today
        end = args.end_date or today
        print(f"Fetching historical air quality (Open-Meteo): {start} → {end}")

        current = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()

        while current <= end_date:
            day_str = str(current)
            print(f"  {day_str}...", end=" ", flush=True)
            data = fetch_historical(day_str, day_str)
            print(f"{len(data['hourly']['time'])} hourly entries", end=" ")

            if not args.no_upload:
                blob_name = f"air_quality/{day_str}.json"
                gcs_path = upload_to_gcs(data, GCS_BUCKET, blob_name)
                print(f"→ uploaded to {gcs_path}")
            else:
                print("(skipped upload)")

            current += timedelta(days=1)

    else:
        print(f"Fetching live AQHI data (type: {args.data_type})...")
        data = fetch_live_aqhi(args.data_type)
        print(f"  {len(data)} records across all stations", end=" ")

        if not args.no_upload:
            timestamp = datetime.now(timezone.utc).strftime("%Y/%m/%d/%H%M%S")
            blob_name = f"air_quality/aqhi/{args.data_type}/{timestamp}.json"
            gcs_path = upload_to_gcs(data, GCS_BUCKET, blob_name)
            print(f"→ uploaded to {gcs_path}")
        else:
            print("(skipped upload)")
