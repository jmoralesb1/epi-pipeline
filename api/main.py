"""
Epi-Pipeline API
Exposes epidemiological surveillance data: weekly trends and anomaly detection.
"""

from pathlib import Path
from typing import Literal

import duckdb
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = Path(__file__).parent.parent / "data" / "epi.duckdb"

app = FastAPI(
    title="Epi-Pipeline API",
    description=(
        "Real-time epidemiological surveillance data. "
        "Covers weekly Influenza, COVID-19, and RSV hospitalizations across US jurisdictions."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_db() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


# --------------------------------------------------------------------------- #
# Response models
# --------------------------------------------------------------------------- #

class WeeklyRecord(BaseModel):
    week_ending_date: str
    resp_season: str | None
    flu_new_admissions: float | None
    covid_new_admissions: float | None
    rsv_new_admissions: float | None
    flu_wow_change: float | None
    covid_wow_change: float | None
    pct_beds_occupied_avg: float | None


class AnomalyRecord(BaseModel):
    week_ending_date: str
    disease: str
    actual: float
    expected: float
    upper_bound: float
    anomaly_score: float


class HealthResponse(BaseModel):
    status: str
    total_weeks: int
    latest_week: str
    anomalies_detected: int


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@app.get("/health", response_model=HealthResponse, tags=["Meta"])
def health():
    """Service health check and data freshness."""
    con = get_db()
    row = con.execute("""
        SELECT
            COUNT(*)                    AS total_weeks,
            MAX(week_ending_date)::text AS latest_week
        FROM fct_respiratory_weekly
    """).fetchone()
    anomalies = con.execute(
        "SELECT COUNT(*) FROM fct_anomalies_weekly WHERE is_anomaly"
    ).fetchone()[0]
    con.close()

    return {
        "status": "ok",
        "total_weeks": row[0],
        "latest_week": row[1],
        "anomalies_detected": anomalies,
    }


@app.get("/weekly", response_model=list[WeeklyRecord], tags=["Surveillance"])
def get_weekly(
    start_date: str | None = Query(None, description="YYYY-MM-DD"),
    end_date: str | None = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(52, ge=1, le=500, description="Number of weeks to return"),
):
    """
    Weekly national respiratory illness metrics (Flu, COVID-19, RSV).
    Returns the most recent weeks by default.
    """
    con = get_db()
    filters = []
    if start_date:
        filters.append(f"week_ending_date >= '{start_date}'")
    if end_date:
        filters.append(f"week_ending_date <= '{end_date}'")

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    rows = con.execute(f"""
        SELECT
            week_ending_date::text,
            resp_season,
            flu_new_admissions,
            covid_new_admissions,
            rsv_new_admissions,
            flu_wow_change,
            covid_wow_change,
            pct_beds_occupied_avg
        FROM fct_respiratory_weekly
        {where}
        ORDER BY week_ending_date DESC
        LIMIT {limit}
    """).fetchall()
    con.close()

    return [
        WeeklyRecord(
            week_ending_date=r[0], resp_season=r[1],
            flu_new_admissions=r[2], covid_new_admissions=r[3],
            rsv_new_admissions=r[4], flu_wow_change=r[5],
            covid_wow_change=r[6], pct_beds_occupied_avg=r[7],
        )
        for r in rows
    ]


@app.get("/anomalies", response_model=list[AnomalyRecord], tags=["Anomaly Detection"])
def get_anomalies(
    disease: Literal["flu", "covid", "rsv"] | None = Query(None),
    min_score: float = Query(0.0, ge=0.0, description="Minimum anomaly score"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Weeks flagged as epidemiologically anomalous by Prophet.
    Anomaly score = how far above the 95% confidence upper bound the actual value is.
    """
    con = get_db()
    filters = ["is_anomaly = true", f"anomaly_score >= {min_score}"]
    if disease:
        filters.append(f"disease = '{disease}'")

    where = "WHERE " + " AND ".join(filters)

    rows = con.execute(f"""
        SELECT
            ds::text,
            disease,
            actual,
            ROUND(yhat, 0),
            ROUND(yhat_upper, 0),
            anomaly_score
        FROM fct_anomalies_weekly
        {where}
        ORDER BY anomaly_score DESC
        LIMIT {limit}
    """).fetchall()
    con.close()

    return [
        AnomalyRecord(
            week_ending_date=r[0], disease=r[1], actual=r[2],
            expected=r[3], upper_bound=r[4], anomaly_score=r[5],
        )
        for r in rows
    ]


@app.get("/anomalies/summary", tags=["Anomaly Detection"])
def anomalies_summary():
    """Summary of anomalies detected per disease."""
    con = get_db()
    rows = con.execute("""
        SELECT
            disease,
            COUNT(*) FILTER (WHERE is_anomaly)               AS anomalous_weeks,
            COUNT(*)                                          AS total_weeks,
            ROUND(MAX(anomaly_score), 3)                      AS max_score,
            (MAX(ds) FILTER (WHERE is_anomaly))::text         AS latest_anomaly
        FROM fct_anomalies_weekly
        GROUP BY disease
        ORDER BY anomalous_weeks DESC
    """).fetchall()
    con.close()

    return [
        {
            "disease": r[0],
            "anomalous_weeks": r[1],
            "total_weeks": r[2],
            "max_anomaly_score": r[3],
            "latest_anomaly": r[4],
        }
        for r in rows
    ]
