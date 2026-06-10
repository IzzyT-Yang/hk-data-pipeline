FROM python:3.11-slim

RUN pip install --no-cache-dir dbt-bigquery==1.11.1

WORKDIR /app/dbt

COPY . .
COPY profiles_prod.yml profiles.yml
