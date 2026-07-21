"""
HK daily ETL — Airflow equivalent of orchestration/daily_etl.yml.

Requires:
  - apache-airflow-providers-docker
  - Docker socket available to the Airflow worker (same as Kestra today)
  - Airflow Variable: GCP_SERVICE_ACCOUNT_KEY (service account JSON string)

Trigger with config / params for backfill, e.g.:
  {"start_date": "2026-06-01", "end_date": "2026-06-07", "run_ingest": true}
"""

from __future__ import annotations

import pendulum
from airflow import DAG
from airflow.models.param import Param
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

GCP_PROJECT = "kestra-sandbox-486905"
INGESTION_IMAGE = f"asia-east2-docker.pkg.dev/{GCP_PROJECT}/hk-pipeline/ingestion:latest"
DBT_IMAGE = f"asia-east2-docker.pkg.dev/{GCP_PROJECT}/hk-pipeline/dbt:latest"

# Same as Kestra: worker talks to local Docker daemon to pull AR images and run containers.
DOCKER_CONN_ID = "docker_default"

COMMON_ENV = {
    "GOOGLE_APPLICATION_CREDENTIALS_JSON": "{{ var.value.GCP_SERVICE_ACCOUNT_KEY }}",
}

START_DATE = "{{ params.start_date or ds }}"
END_DATE = "{{ params.end_date or ds }}"


def _branch(param_name: str, run_task_id: str, skip_task_id: str):
    def _choose(**context):
        if context["params"].get(param_name, True):
            return run_task_id
        return skip_task_id

    return _choose


with DAG(
    dag_id="hk_daily_etl",
    description="Ingest Open-Meteo → GCS → BigQuery → dbt (replaces Kestra daily_pipeline)",
    schedule="0 8 * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Hong_Kong"),
    catchup=False,
    max_active_runs=1,
    tags=["hk_data_pipeline"],
    params={
        "start_date": Param(default="", type="string", description="YYYY-MM-DD; empty = logical date"),
        "end_date": Param(default="", type="string", description="YYYY-MM-DD; empty = logical date"),
        "run_ingest": Param(default=True, type="boolean"),
        "run_load": Param(default=True, type="boolean"),
        "run_transform": Param(default=True, type="boolean"),
    },
    render_template_as_native_obj=True,
) as dag:
    start = EmptyOperator(task_id="start")

    # --- Ingest (optional) ---
    branch_ingest = BranchPythonOperator(
        task_id="branch_ingest",
        python_callable=_branch("run_ingest", "run_ingest", "skip_ingest"),
    )
    run_ingest = EmptyOperator(task_id="run_ingest")
    skip_ingest = EmptyOperator(task_id="skip_ingest")

    with TaskGroup(group_id="ingest") as ingest_group:
        DockerOperator(
            task_id="weather",
            image=INGESTION_IMAGE,
            api_version="auto",
            auto_remove="success",
            docker_url="unix://var/run/docker.sock",
            network_mode="bridge",
            command=[
                "python",
                "/app/weather_report.py",
                "--start-date",
                START_DATE,
                "--end-date",
                END_DATE,
            ],
            environment=COMMON_ENV,
            docker_conn_id=DOCKER_CONN_ID,
        )
        DockerOperator(
            task_id="air_quality",
            image=INGESTION_IMAGE,
            api_version="auto",
            auto_remove="success",
            docker_url="unix://var/run/docker.sock",
            network_mode="bridge",
            command=[
                "python",
                "/app/air_quality.py",
                "--start-date",
                START_DATE,
                "--end-date",
                END_DATE,
            ],
            environment=COMMON_ENV,
            docker_conn_id=DOCKER_CONN_ID,
        )

    join_ingest = EmptyOperator(
        task_id="join_ingest",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # --- Load (optional) ---
    branch_load = BranchPythonOperator(
        task_id="branch_load",
        python_callable=_branch("run_load", "run_load", "skip_load"),
    )
    run_load = EmptyOperator(task_id="run_load")
    skip_load = EmptyOperator(task_id="skip_load")

    with TaskGroup(group_id="load") as load_group:
        DockerOperator(
            task_id="weather",
            image=INGESTION_IMAGE,
            api_version="auto",
            auto_remove="success",
            docker_url="unix://var/run/docker.sock",
            network_mode="bridge",
            command=[
                "python",
                "/app/gcs_to_bq.py",
                "--source",
                "weather",
                "--start-date",
                START_DATE,
                "--end-date",
                END_DATE,
            ],
            environment=COMMON_ENV,
            docker_conn_id=DOCKER_CONN_ID,
        )
        DockerOperator(
            task_id="air_quality",
            image=INGESTION_IMAGE,
            api_version="auto",
            auto_remove="success",
            docker_url="unix://var/run/docker.sock",
            network_mode="bridge",
            command=[
                "python",
                "/app/gcs_to_bq.py",
                "--source",
                "air_quality",
                "--start-date",
                START_DATE,
                "--end-date",
                END_DATE,
            ],
            environment=COMMON_ENV,
            docker_conn_id=DOCKER_CONN_ID,
        )

    join_load = EmptyOperator(
        task_id="join_load",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # --- Transform (optional) ---
    branch_transform = BranchPythonOperator(
        task_id="branch_transform",
        python_callable=_branch("run_transform", "run_transform", "skip_transform"),
    )
    run_transform = EmptyOperator(task_id="run_transform")
    skip_transform = EmptyOperator(task_id="skip_transform")

    dbt_run = DockerOperator(
        task_id="dbt_run",
        image=DBT_IMAGE,
        api_version="auto",
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        command=(
            "python3 -c \"import os; open('/tmp/keyfile.json','w').write("
            "os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON'])\" && "
            "dbt run --project-dir /app/dbt --profiles-dir /app/dbt "
            "--vars '{\"start_date\": \"{{ params.start_date or ds }}\", "
            "\"end_date\": \"{{ params.end_date or ds }}\"}'"
        ),
        environment=COMMON_ENV,
        docker_conn_id=DOCKER_CONN_ID,
    )

    join_transform = EmptyOperator(
        task_id="join_transform",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )
    end = EmptyOperator(task_id="end", trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)

    start >> branch_ingest >> [run_ingest, skip_ingest]
    run_ingest >> ingest_group >> join_ingest
    skip_ingest >> join_ingest

    join_ingest >> branch_load >> [run_load, skip_load]
    run_load >> load_group >> join_load
    skip_load >> join_load

    join_load >> branch_transform >> [run_transform, skip_transform]
    run_transform >> dbt_run >> join_transform
    skip_transform >> join_transform

    join_transform >> end
