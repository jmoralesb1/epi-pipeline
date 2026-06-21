"""Generate the weekly Markdown surveillance report from DuckDB results."""

from pathlib import Path
from datetime import date
import json
import duckdb

DB_PATH = Path(__file__).parent.parent / 'data' / 'epi.duckdb'
REPORTS_DIR = Path(__file__).parent.parent / 'reports'
DBT_RESULTS_PATH = Path(__file__).parent.parent / 'dbt' / 'target' / 'run_results.json'


def load_dbt_test_status():
    if not DBT_RESULTS_PATH.exists():
        return 'N/A'
    with open(DBT_RESULTS_PATH) as f:
        results = json.load(f)
    tests = [r for r in results.get('results', []) if 'test' in r.get('unique_id', '')]
    passed = sum(1 for t in tests if t.get('status') == 'pass')
    failed = sum(1 for t in tests if t.get('status') not in ('pass', 'warn'))
    total = len(tests)
    return f'{passed}/{total} PASS' if failed == 0 else f'{passed}/{total} PASS, {failed} FAIL'


def format_anomaly_table(rows):
    lines = [
        '| Date | Actual Admissions | Expected (yhat) | Upper Bound | Anomaly Score |',
        '|------|-------------------|-----------------|-------------|---------------|',
    ]
    for _, r in rows.iterrows():
        lines.append(
            f"| {str(r['ds'])[:10]} | {int(r['actual']):,} | {int(r['yhat']):,} "
            f"| {int(r['yhat_upper']):,} | {r['anomaly_score']:.4f} |"
        )
    return '\n'.join(lines)


def disease_section(anom_df, disease_code, display_name, top_n=15):
    subset = anom_df[(anom_df['disease'] == disease_code) & anom_df['is_anomaly']]
    total = len(subset)
    top = subset.sort_values('anomaly_score', ascending=False).head(top_n)
    extra = max(0, total - len(top))
    table = format_anomaly_table(top)
    note = (
        f'\n*({extra} additional lower-scoring {display_name} anomalies omitted; '
        f'full results in `fct_anomalies_weekly`)*'
    ) if extra else ''
    return f'### {display_name} - {total} anomalous weeks\n\n{table}{note}'


def main():
    today = date.today().isoformat()
    con = duckdb.connect(str(DB_PATH))

    summary = con.execute("""
        SELECT disease,
               COUNT(*) AS records,
               SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) AS anomalous_weeks,
               MAX(ds) AS latest_week
        FROM fct_anomalies_weekly
        GROUP BY disease ORDER BY disease
    """).df()

    anom = con.execute('SELECT * FROM fct_anomalies_weekly').df()

    date_range = con.execute("""
        SELECT MIN(week_ending_date), MAX(week_ending_date), COUNT(*)
        FROM fct_respiratory_weekly
    """).fetchone()

    latest = con.execute("""
        SELECT week_ending_date, flu_new_admissions, covid_new_admissions, rsv_new_admissions
        FROM fct_respiratory_weekly ORDER BY week_ending_date DESC LIMIT 1
    """).fetchone()

    ingested = con.execute('SELECT COUNT(*) FROM stg_nhsn_hrd').fetchone()[0]
    con.close()

    def summary_row(code, name):
        row = summary[summary['disease'] == code]
        if row.empty:
            return f'| {name} | N/A | N/A | N/A |'
        r = row.iloc[0]
        return f"| {name} | {int(r['records'])} | {int(r['anomalous_weeks'])} | {str(r['latest_week'])[:10]} |"

    dbt_status = load_dbt_test_status()

    report = f"""# Weekly Epidemiological Surveillance Report
**Date:** {today}
**Data source:** CDC NHSN Hospital Respiratory Data (ua7e-t2fy)
**Pipeline run:** automated weekly

---

## Summary

| Disease | Records | Anomalous Weeks | Latest Week |
|---------|---------|-----------------|-------------|
{summary_row('flu', 'Influenza')}
{summary_row('covid', 'COVID-19')}
{summary_row('rsv', 'RSV')}

**Latest week admissions ({latest[0]}):** Flu {int(latest[1]):,} - COVID-19 {int(latest[2]):,} - RSV {int(latest[3]):,}

---

## Anomalies Detected This Run

Anomaly method: rolling 52-week baseline (mean +/- 2 SD).

{disease_section(anom, 'flu', 'Influenza')}

{disease_section(anom, 'covid', 'COVID-19')}

{disease_section(anom, 'rsv', 'RSV')}

---

## Data Quality

- **dbt tests:** {dbt_status}
- **Records ingested:** {ingested:,}
- **Date range covered:** {date_range[0]} to {date_range[1]}
- **Anomaly detection method:** Rolling 52-week baseline (mean +/- 2 SD)
- **dbt models materialized:** `stg_nhsn_hrd` (view), `fct_respiratory_weekly` (table)
- **Anomaly table:** `fct_anomalies_weekly` - {len(anom):,} rows
"""

    REPORTS_DIR.mkdir(exist_ok=True)
    out = REPORTS_DIR / f'weekly_report_{today}.md'
    out.write_text(report)
    print(f'Report written to {out}')


if __name__ == '__main__':
    main()
