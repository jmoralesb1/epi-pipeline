"""
Anomaly Detection: Weekly Respiratory Illness Surveillance
Uses Prophet to detect anomalous spikes in Flu, COVID-19, and RSV admissions.

Method:
- Train Prophet on historical data (rolling window)
- Compare actual vs predicted + uncertainty interval
- Flag weeks where actual > upper bound (anomaly score > 0)
"""

from pathlib import Path

import duckdb
import pandas as pd
from prophet import Prophet

DB_PATH = Path(__file__).parent.parent / "data" / "epi.duckdb"
OUTPUT_TABLE = "fct_anomalies_weekly"


def load_gold_data(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("""
        SELECT
            week_ending_date  AS ds,
            flu_new_admissions,
            covid_new_admissions,
            rsv_new_admissions
        FROM fct_respiratory_weekly
        WHERE week_ending_date IS NOT NULL
        ORDER BY ds
    """).df()


def detect_anomalies_for_series(
    df: pd.DataFrame,
    value_col: str,
    min_training_weeks: int = 52,
) -> pd.DataFrame:
    """
    Fits Prophet on each series and flags anomalies.
    An anomaly is a week where actual > yhat_upper (outside 95% interval).
    """
    series = df[["ds", value_col]].rename(columns={value_col: "y"}).dropna()

    if len(series) < min_training_weeks:
        print(f"  Not enough data for {value_col} ({len(series)} weeks)")
        return pd.DataFrame()

    model = Prophet(
        interval_width=0.95,
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,  # conservative — epidemics are real signals
    )

    model.fit(series)
    forecast = model.predict(series[["ds"]])

    result = series.merge(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]], on="ds")
    result["disease"] = value_col.replace("_new_admissions", "")
    result["is_anomaly"] = result["y"] > result["yhat_upper"]
    result["anomaly_score"] = ((result["y"] - result["yhat_upper"]) / result["yhat_upper"]).clip(lower=0).round(4)

    return result.rename(columns={"y": "actual"})


def run(con: duckdb.DuckDBPyConnection) -> None:
    print("Loading Gold layer data...")
    df = load_gold_data(con)
    print(f"  {len(df)} weeks loaded ({df.ds.min().date()} → {df.ds.max().date()})")

    diseases = ["flu_new_admissions", "covid_new_admissions", "rsv_new_admissions"]
    all_results = []

    for col in diseases:
        print(f"\nFitting Prophet for {col}...")
        result = detect_anomalies_for_series(df, col)
        if not result.empty:
            anomalies = result["is_anomaly"].sum()
            print(f"  {anomalies} anomalous weeks detected out of {len(result)}")
            all_results.append(result)

    if not all_results:
        print("No results to save.")
        return

    combined = pd.concat(all_results, ignore_index=True)

    con.execute(f"DROP TABLE IF EXISTS {OUTPUT_TABLE}")
    con.execute(f"""
        CREATE TABLE {OUTPUT_TABLE} AS
        SELECT * FROM combined
    """)

    print(f"\nSaved {len(combined)} rows to table '{OUTPUT_TABLE}'")


if __name__ == "__main__":
    con = duckdb.connect(str(DB_PATH))
    run(con)
    con.close()
    print("\nDone.")
