"""
DAG: CDC FluView Ingestion
Pulls weekly influenza surveillance data from CDC FluView API
and stores it as Parquet in the raw layer.
"""

from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

RAW_DIR = Path("/Users/jaidermorales/Dev/epi-pipeline/data/raw/fluview")
CDC_FLUVIEW_URL = "https://data.cdc.gov/resource/ph9p-i8ad.json"


def ingest_fluview(**context):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    ingestion_ts = context["logical_date"].strftime("%Y%m%d_%H%M%S")
    limit = 1000
    offset = 0
    records = []

    while True:
        response = httpx.get(
            CDC_FLUVIEW_URL,
            params={"$limit": limit, "$offset": offset},
            timeout=30,
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        records.extend(batch)
        offset += limit

    df = pd.DataFrame(records)
    df["_ingested_at"] = datetime.utcnow().isoformat()

    output_path = RAW_DIR / f"fluview_{ingestion_ts}.parquet"
    df.to_parquet(output_path, index=False)
    print(f"Ingested {len(df)} records → {output_path}")


default_args = {
    "owner": "epi-pipeline",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="cdc_fluview_ingestion",
    description="Weekly CDC FluView influenza surveillance ingestion",
    schedule_interval="0 8 * * 1",  # Every Monday at 8am
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["cdc", "influenza", "ingestion"],
) as dag:
    ingest = PythonOperator(
        task_id="ingest_fluview",
        python_callable=ingest_fluview,
    )
