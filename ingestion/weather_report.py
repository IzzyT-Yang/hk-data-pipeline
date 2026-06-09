import argparse
import requests
from datetime import datetime, timezone, timedelta
from utils import GCS_BUCKET, LATITUDE, LONGITUDE, TIMEZONE, upload_to_gcs

HOURLY_VARS = "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m,weather_code"

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def _base_params() -> dict:
    return {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": HOURLY_VARS,
        "timezone": TIMEZONE,
    }


def _merge(a: dict, b: dict) -> dict:
    merged = {**a}
    for key, values in b["hourly"].items():
        merged["hourly"][key].extend(values)
    return merged


def fetch_weather(start_date: str, end_date: str) -> dict:
    today = datetime.now(timezone.utc).date()
    archive_cutoff = today - timedelta(days=5)

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    if end <= archive_cutoff:
        params = {**_base_params(), "start_date": start_date, "end_date": end_date}
        r = requests.get(ARCHIVE_URL, params=params)
        r.raise_for_status()
        return r.json()

    if start > archive_cutoff:
        forecast_days = min((end - today).days + 1 + (today - start).days, 16)
        params = {**_base_params(), "forecast_days": max(1, forecast_days)}
        r = requests.get(FORECAST_URL, params=params)
        r.raise_for_status()
        return r.json()

    archive_params = {**_base_params(), "start_date": start_date, "end_date": str(archive_cutoff)}
    r_archive = requests.get(ARCHIVE_URL, params=archive_params)
    r_archive.raise_for_status()

    forecast_days = min((end - today).days + 1 + 5, 16)
    forecast_params = {**_base_params(), "forecast_days": max(1, forecast_days)}
    r_forecast = requests.get(FORECAST_URL, params=forecast_params)
    r_forecast.raise_for_status()

    return _merge(r_archive.json(), r_forecast.json())


if __name__ == "__main__":
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(description="Fetch HK weather from Open-Meteo")
    parser.add_argument("--start-date", default=today, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=today, help="End date (YYYY-MM-DD)")
    parser.add_argument("--no-upload", action="store_true", help="Skip GCS upload")
    args = parser.parse_args()

    print(f"Fetching weather: {args.start_date} → {args.end_date}")

    current = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()

    while current <= end_date:
        day_str = str(current)
        print(f"  {day_str}...", end=" ", flush=True)
        data = fetch_weather(day_str, day_str)
        print(f"{len(data['hourly']['time'])} hourly entries", end=" ")

        if not args.no_upload:
            blob_name = f"weather/{day_str}.json"
            gcs_path = upload_to_gcs(data, GCS_BUCKET, blob_name)
            print(f"→ uploaded to {gcs_path}")
        else:
            print("(skipped upload)")

        current += timedelta(days=1)
