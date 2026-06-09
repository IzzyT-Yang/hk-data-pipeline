# HK Data Pipeline

A end-to-end data engineering project ingesting Hong Kong weather and transport data into BigQuery, transformed with dbt, orchestrated by Kestra, and visualized in Looker Studio.

## Architecture

```
HKO API / Transport API
        │
        ▼
  Python EL Scripts (ingestion/)
        │
        ▼
  GCS (raw bucket)
        │
        ▼
  BigQuery (raw dataset)
        │
        ▼
  dbt (staging → mart)
        │
        ▼
  Looker Studio Dashboard
```

> Architecture diagram and dashboard screenshots coming soon.

## Stack

| Layer | Tool |
|---|---|
| Ingestion | Python |
| Storage | GCS + BigQuery |
| Transformation | dbt |
| Orchestration | Kestra |
| Visualization | Looker Studio |

## Project Structure

```
hk-data-pipeline/
├── ingestion/        # Python EL scripts
├── dbt/              # dbt project (staging + mart models)
├── orchestration/    # Kestra YAML flows
├── infra/            # Terraform (GCS bucket, BQ dataset)
└── dashboard/        # Looker Studio screenshots / embed links
```

## Setup

### 1. Ingestion
```bash
cd ingestion
pip install -r requirements.txt
python hko_weather.py
python transport.py
```

### 2. dbt
```bash
cd dbt
cp profiles.yml.example profiles.yml  # fill in your BigQuery credentials
dbt deps
dbt run
```

### 3. Orchestration
Import the YAML flows in `orchestration/` into your Kestra instance.

## Dashboard

> Screenshots and embed links will be added here once the dashboard is live.
