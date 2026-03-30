"""
DAG: CDC NHSN Weekly Hospital Respiratory Data Ingestion
Dataset: ua7e-t2fy — Weekly Hospital Respiratory Data (HRD) Metrics by Jurisdiction
Source: National Healthcare Safety Network (NHSN) via data.cdc.gov

Covers: Influenza, COVID-19, RSV hospitalizations by state, weekly.
"""

from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

RAW_DIR = Path("/Users/jaidermorales/Dev/epi-pipeline/data/raw/nhsn_hrd")
CDC_NHSN_URL = "https://data.cdc.gov/resource/ua7e-t2fy.json"

# Columns relevant to epidemiological surveillance
COLUMNS_OF_INTEREST = [
    "weekendingdate",
    "jurisdiction",
    "respseason",
    "totalconfflunewadm",
    "totalconffluhosppats",
    "totalconffluicupats",
    "totalconfc19newadm",
    "totalconfc19hosppats",
    "totalconfc19icupats",
    "totalconfrsvnewadm",
    "totalconfflunewadmper100k",
    "totalconfc19newadmper100k",
    "totalconfflunewadmcumulativeseasonalsum",
    "totalconfc19newadmcumulativeseasonalsum",
    "totalconfrsvnewadmcumulativeseasonalsum",
    "numinptbeds",
    "numinptbedsocc",
    "pctinptbedsocc",
]


def ingest_nhsn_hrd(**context):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    ingestion_ts = context["logical_date"].strftime("%Y%m%d_%H%M%S")
    limit = 5000
    offset = 0
    records = []

    print(f"Starting ingestion from {CDC_NHSN_URL}")

    while True:
        response = httpx.get(
            CDC_NHSN_URL,
            params={"$limit": limit, "$offset": offset, "$order": "weekendingdate DESC"},
            timeout=60,
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        records.extend(batch)
        offset += limit
        print(f"  Fetched {offset} records so far...")

        # Stop at 100k records for initial ingestion (full history on first run)
        if offset >= 100_000:
            break

    df = pd.DataFrame(records)

    # Keep only columns of interest that exist in the response
    existing_cols = [c for c in COLUMNS_OF_INTEREST if c in df.columns]
    df = df[existing_cols].copy()

    df["_ingested_at"] = datetime.utcnow().isoformat()

    output_path = RAW_DIR / f"nhsn_hrd_{ingestion_ts}.parquet"
    df.to_parquet(output_path, index=False)
    print(f"Ingested {len(df)} records → {output_path}")
    return str(output_path)


default_args = {
    "owner": "epi-pipeline",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="cdc_nhsn_hrd_ingestion",
    description="Weekly CDC NHSN Hospital Respiratory Data ingestion (Flu, COVID-19, RSV)",
    schedule_interval="0 8 * * 3",  # Every Wednesday at 8am (CDC publishes Wednesdays)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["cdc", "nhsn", "influenza", "covid19", "rsv", "ingestion"],
) as dag:
    ingest = PythonOperator(
        task_id="ingest_nhsn_hrd",
        python_callable=ingest_nhsn_hrd,
    )
