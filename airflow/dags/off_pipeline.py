from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

with DAG(
    dag_id="off_pipeline",
    description="OFF ingestion and dbt pipeline",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["off"],
) as dag:

    download_delta_index = BashOperator(
        task_id="download_delta_index",
        bash_command=(
            "cd /opt/project && " "python ingestion/deltas/download_delta_index.py"
        ),
    )

    register_delta_files = BashOperator(
        task_id="register_delta_files",
        bash_command=(
            "cd /opt/project && " "python ingestion/deltas/register_delta_files.py"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="""
        cd /opt/project/dbt_project &&
        dbt run --profiles-dir .
        """,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="""
        cd /opt/project/dbt_project &&
        dbt test --profiles-dir .
        """,
    )

    download_delta_index >> register_delta_files >> dbt_run >> dbt_test
