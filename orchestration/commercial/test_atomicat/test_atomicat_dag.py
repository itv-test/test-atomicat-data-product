from datetime import datetime
from airflow import DAG
from itv.data.airflow.slack import failure_alert
from itv.data.airflow.dataproc import ITVDataprocCreateBatchOperator

DATA_PRODUCT_NAME = "test-atomicat"
DOMAIN = "commercial"
DATAPROC_SERVERLESS_RUNTIME_VERSION = "3.0"
env = '{{ var.value.get("platform-environment", "dev") }}'
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "on_failure_callback": failure_alert(
        alert_title="test-atomicat Task Failed",
        slack_channel="tmp-data-cortex-{env}-alerts",
    ),
}

readme_url = "https://github.com/ITV/test-atomicat-data-product/blob/main/orchestration/README.md"
documentation_markdown = f"""
### README

The README for this DAG is [available on GitHub]({readme_url}).
"""

with DAG(
    "test_atomicat_dag",
    start_date=datetime(year=2025, month=1, day=1),
    schedule_interval=None,
    catchup=False,
    default_args=default_args,
    tags=[
        f"data-product:{DATA_PRODUCT_NAME}",
        f"domain:{DOMAIN}",
    ],
    doc_md=documentation_markdown,
) as dag:

    ingest_task = ITVDataprocCreateBatchOperator(
        task_id="ingest_task",
        domain=DOMAIN,
        data_product_name=DATA_PRODUCT_NAME,
        entry_point="test_atomicat/ingest/main.py",
        runtime_version=DATAPROC_SERVERLESS_RUNTIME_VERSION,
        runtime_args=[
            "--project-id",
            '{{ var.value.get("platform-commercial-project-id", "itv-data-commercial-dom-dev") }}',
            "--region",
            '{{ var.value.get("platform-region", "europe-west2") }}',
            "--env",
            '{{ var.value.get("platform-environment", "dev") }}',
            "--data-product-bucket-path",
            'gs://itv-data-dp-test-atomicat-{{ var.value.get("platform-environment", "dev") }}',
        ],
    )

    ingest_task
