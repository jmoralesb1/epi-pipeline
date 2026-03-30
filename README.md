# epi-pipeline

Real-time epidemiological surveillance data pipeline addressing latency gaps in CDC NNDSS reporting.

## Problem

CDC NNDSS data is published with 1-2 week latency in inconsistent formats across states.
This pipeline integrates multiple public health data sources to reduce that lag and enable
near-real-time anomaly detection.

## Architecture

```
Sources (CDC NNDSS, FluView, HealthData.gov, Wastewater)
  → Ingestion (Airflow DAGs)
    → Raw Layer (Parquet / DuckDB)
      → Transformation (dbt)
        → Analytics (Prophet anomaly detection)
          → API (FastAPI)
```

## Stack

- **Orchestration**: Apache Airflow
- **Storage**: DuckDB + Parquet
- **Transformation**: dbt
- **Data quality**: Great Expectations
- **Anomaly detection**: Prophet
- **API**: FastAPI

## Structure

```
epi-pipeline/
├── dags/          # Airflow DAGs (ingestion pipelines)
├── dbt/           # dbt models (Silver / Gold layers)
├── data/          # Local data (gitignored)
├── notebooks/     # Exploratory analysis
├── api/           # FastAPI service
├── tests/         # Unit and integration tests
└── docs/          # Documentation and paper drafts
```

## Data Sources

- CDC NNDSS Weekly Tables: https://wonder.cdc.gov/nndss/
- CDC FluView API: https://data.cdc.gov
- Google Wastewater Surveillance: BigQuery public dataset

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
