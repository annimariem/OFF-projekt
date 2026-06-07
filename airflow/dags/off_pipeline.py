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

    check_bootstrap = BashOperator(
        task_id="check_bootstrap",
        bash_command="""
        python - <<'PY'
import os
import psycopg2

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)

with conn.cursor() as cur:
    cur.execute('''
        SELECT EXISTS (
            SELECT 1
            FROM raw.bootstrap_load_runs
            WHERE status = 'SUCCESS'
        )
    ''')

    count = cur.fetchone()[0]

    if count == 0:
        raise RuntimeError(
            "Bootstrap dataset ei ole warehouse'isse laetud. "
            "Käivita ingestion/bootstrap/load_bootstrap_snapshot.py"
        )
PY
        """,
    )

    download_delta_index = BashOperator(
        task_id="download_delta_index",
        bash_command=(
            "cd /opt/project && " "python ingestion/deltas/download_delta_index.py"
        ),
    )

    register_deltas = BashOperator(
        task_id="register_deltas",
        bash_command=(
            "cd /opt/project && " "python ingestion/deltas/register_delta_files.py"
        ),
    )

    download_deltas = BashOperator(
        task_id="download_deltas",
        bash_command=(
            "cd /opt/project && " "python ingestion/deltas/download_new_deltas.py"
        ),
    )

    process_deltas = BashOperator(
        task_id="process_deltas",
        bash_command=(
            "cd /opt/project && " "python ingestion/deltas/process_delta_file.py"
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

    (
        check_bootstrap
        >> download_delta_index
        >> register_deltas
        >> download_deltas
        >> process_deltas
        >> dbt_run
        >> dbt_test
    )
