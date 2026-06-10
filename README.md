# HK Data Pipeline

An end-to-end data engineering project that ingests Hong Kong weather and air quality data from Open-Meteo, loads it into BigQuery, transforms it with dbt, orchestrates daily runs with Kestra on GCP, and visualizes results in Looker Studio.

## Architecture

```
Open-Meteo API (weather + air quality)
        │
        ▼
  Python ingestion scripts
  (weather_report.py, air_quality.py)
        │
        ▼
  GCS — raw JSON files (one per day per source)
        │
        ▼
  BigQuery — raw tables
  (gcs_to_bq.py, batched load)
        │
        ▼
  dbt — staging (dedup) → mart (daily aggregations) → combined
        │
        ▼
  Looker Studio Dashboard
```

## Stack

| Layer | Tool |
|---|---|
| Data source | Open-Meteo API (weather + air quality) |
| Ingestion | Python + GCS |
| Storage | Google Cloud Storage + BigQuery |
| Transformation | dbt (BigQuery adapter) |
| Orchestration | Kestra (self-hosted on GCP VM) |
| Containerization | Docker + Artifact Registry |
| Visualization | Looker Studio |

## Project Structure

```
hk-data-pipeline/
├── ingestion/
│   ├── weather_report.py   # Open-Meteo weather → GCS
│   ├── air_quality.py      # Open-Meteo air quality → GCS
│   ├── gcs_to_bq.py        # GCS → BigQuery (batched)
│   ├── utils.py            # shared GCS upload + GCP credentials
│   ├── requirements.txt
│   └── Dockerfile
├── dbt/
│   ├── models/
│   │   ├── staging/        # dedup raw data
│   │   └── mart/           # daily aggregations + combined
│   ├── profiles_prod.yml
│   └── Dockerfile
├── orchestration/
│   ├── ingest.yml          # subflow: fetch API → GCS
│   ├── load.yml            # subflow: GCS → BigQuery
│   ├── transform.yml       # subflow: dbt run
│   ├── daily_etl.yml       # main pipeline (ingest + load + transform)
│   └── push_flows.sh       # push all flows to Kestra via API
├── docker-compose.yml      # local Kestra for development
└── dashboard/              # Looker Studio screenshots
```

## dbt Models

```
raw.weather / raw.air_quality
        │
        ▼
staging.stg_weather / staging.stg_air_quality   (deduplicated views)
        │
        ▼
mart.mart_daily_weather                          (daily weather aggregations)
mart.mart_daily_air_quality                      (daily AQI aggregations)
        │
        ▼
mart.mart_daily_combined                         (joined weather + air quality)
```

## Setup

### Prerequisites
- GCP project with BigQuery, GCS, and Artifact Registry enabled
- Docker Desktop
- `gcloud` CLI authenticated

### 1. Local development

```bash
# install dependencies
cd ingestion && pip install -r requirements.txt

# run ingestion locally (today's data)
python weather_report.py
python air_quality.py

# load to BigQuery
python gcs_to_bq.py

# run dbt
cd ../dbt && dbt run --profiles-dir . --project-dir .
```

### 2. Build and push Docker images

```bash
docker build -t asia-east2-docker.pkg.dev/<project>/hk-pipeline/ingestion:latest ./ingestion
docker build -t asia-east2-docker.pkg.dev/<project>/hk-pipeline/dbt:latest ./dbt
docker push asia-east2-docker.pkg.dev/<project>/hk-pipeline/ingestion:latest
docker push asia-east2-docker.pkg.dev/<project>/hk-pipeline/dbt:latest
```

### 3. Kestra (local)

```bash
docker compose up -d
# UI at http://localhost:8080
```

### 4. Deploy flows to Kestra

```bash
cd orchestration && ./push_flows.sh
```

### 5. Configure KV Store

In the Kestra UI: **Namespaces → hk_data_pipeline → KV Store**

| Key | Value |
|-----|-------|
| `GCP_SERVICE_ACCOUNT_KEY` | GCP service account JSON |

### 6. Run the pipeline

- **Daily (automated)**: schedule trigger runs at 08:00 HKT
- **Manual / backfill**: trigger `daily_pipeline` with custom `start_date` and `end_date`; toggle `run_ingest`, `run_load`, `run_transform` as needed

## Dashboard

[View Live Dashboard](https://datastudio.google.com/reporting/967f5202-3002-48b0-990b-cb67b4eabd59)

![HK Air Quality Data Analysis](dashboard/HK%20Air%20Quality%20Data%20Analysis.png)
