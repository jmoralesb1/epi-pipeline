"""
Anomaly detection using a rolling 52-week baseline (mean +/- 2 SD).
Writes results to the fct_anomalies_weekly table in DuckDB.
"""

from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

DB_PATH = Path(__file__).parent.parent / 'data' / 'epi.duckdb'
OUTPUT_TABLE = 'fct_anomalies_weekly'
ROLLING_WINDOW = 52


def load_gold_data(con):
    return con.execute("""
        SELECT
            week_ending_date AS ds,
            flu_new_admissions,
            covid_new_admissions,
            rsv_new_admissions
        FROM fct_respiratory_weekly
        WHERE week_ending_date IS NOT NULL
        ORDER BY ds
    """).df()


def detect_anomalies_for_series(df, value_col, min_training_weeks=52):
    series = df[['ds', value_col]].rename(columns={value_col: 'y'}).dropna()
    if len(series) < min_training_weeks:
        print(f'  Not enough data for {value_col} ({len(series)} weeks)')
        return pd.DataFrame()

    rolling = series['y'].shift(1).rolling(window=ROLLING_WINDOW, min_periods=max(4, ROLLING_WINDOW // 4))
    yhat = rolling.mean()
    ystd = rolling.std()

    result = series.copy()
    result['yhat'] = yhat
    result['yhat_lower'] = yhat - 2.0 * ystd
    result['yhat_upper'] = yhat + 2.0 * ystd
    result['disease'] = value_col.replace('_new_admissions', '')
    result['is_anomaly'] = result['y'] > result['yhat_upper']
    result['anomaly_score'] = (
        ((result['y'] - result['yhat_upper']) / result['yhat_upper'].replace(0, np.nan))
        .clip(lower=0)
        .round(4)
    )

    return result.dropna(subset=['yhat']).rename(columns={'y': 'actual'})


def run(con):
    print('Loading Gold layer data...')
    df = load_gold_data(con)
    print(f'  {len(df)} weeks loaded ({df.ds.min().date()} -> {df.ds.max().date()})')

    all_results = []
    for col in ['flu_new_admissions', 'covid_new_admissions', 'rsv_new_admissions']:
        print(f'\nFitting rolling-baseline model for {col}...')
        result = detect_anomalies_for_series(df, col)
        if not result.empty:
            print(f'  {result["is_anomaly"].sum()} anomalous weeks out of {len(result)}')
            all_results.append(result)

    if not all_results:
        print('No results to save.')
        return

    combined = pd.concat(all_results, ignore_index=True)
    con.execute(f'DROP TABLE IF EXISTS {OUTPUT_TABLE}')
    con.execute(f'CREATE TABLE {OUTPUT_TABLE} AS SELECT * FROM combined')
    print(f"\nSaved {len(combined)} rows to table '{OUTPUT_TABLE}'")


if __name__ == '__main__':
    con = duckdb.connect(str(DB_PATH))
    run(con)
    con.close()
    print('\nDone.')
