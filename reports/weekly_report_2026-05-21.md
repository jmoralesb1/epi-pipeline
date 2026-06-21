# Weekly Epidemiological Surveillance Report
**Date:** 2026-05-21  
**Data source:** CDC NHSN Hospital Respiratory Data (ua7e-t2fy)  
**Pipeline run:** automated weekly

---

## Summary

| Disease | Records | Anomalous Weeks | Latest Week |
|---------|---------|-----------------|-------------|
| Influenza | 281 | 45 | 2026-03-21 |
| COVID-19 | 281 | 14 | 2026-03-21 |
| RSV | 116 | 16 | 2026-03-21 |

**Latest week admissions (2026-03-21):** Flu 16,920 · COVID-19 11,271 · RSV 18,798

---

## Anomalies Detected This Run

Anomaly method: rolling 52-week baseline (mean ± 2 SD). Anomaly score = (actual − upper_bound) / upper_bound, clipped to zero.

### Influenza — 45 anomalous weeks

| Date | Actual Admissions | Expected (yhat) | Upper Bound | Anomaly Score |
|------|-------------------|-----------------|-------------|---------------|
| 2022-12-03 | 80,421 | 7,369 | 25,080 | 2.2066 |
| 2022-11-26 | 54,426 | 6,349 | 18,119 | 2.0037 |
| 2022-01-01 | 8,937 | 1,287 | 3,031 | 1.9481 |
| 2025-01-04 | 118,884 | 14,261 | 51,551 | 1.3061 |
| 2022-11-19 | 32,778 | 5,740 | 14,927 | 1.1959 |
| 2021-12-25 | 5,364 | 1,227 | 2,568 | 1.0889 |
| 2022-11-12 | 25,707 | 5,265 | 12,611 | 1.0384 |
| 2023-12-30 | 65,001 | 8,289 | 32,076 | 1.0265 |
| 2022-12-10 | 71,979 | 8,865 | 35,723 | 1.0149 |
| 2025-02-01 | 157,578 | 19,158 | 81,345 | 0.9372 |
| 2024-12-28 | 85,920 | 13,858 | 48,341 | 0.7774 |
| 2025-02-08 | 166,668 | 21,498 | 94,476 | 0.7641 |
| 2024-01-06 | 58,506 | 8,417 | 33,347 | 0.7545 |
| 2025-01-25 | 124,206 | 17,518 | 72,485 | 0.7135 |
| 2022-11-05 | 19,191 | 4,915 | 11,216 | 0.7110 |

*(30 additional lower-scoring Influenza anomalies omitted; full results in `fct_anomalies_weekly`)*

### COVID-19 — 14 anomalous weeks

| Date | Actual Admissions | Expected (yhat) | Upper Bound | Anomaly Score |
|------|-------------------|-----------------|-------------|---------------|
| 2022-01-15 | 468,000 | 159,567 | 332,806 | 0.4062 |
| 2020-11-14 | 222,426 | 113,650 | 166,816 | 0.3334 |
| 2020-11-21 | 259,266 | 120,902 | 196,928 | 0.3166 |
| 2022-01-08 | 423,456 | 158,774 | 327,403 | 0.2934 |
| 2022-01-22 | 439,359 | 161,700 | 347,161 | 0.2656 |
| 2020-11-07 | 177,027 | 108,775 | 149,028 | 0.1879 |
| 2020-11-28 | 272,706 | 129,549 | 230,450 | 0.1834 |
| 2020-12-05 | 304,770 | 137,970 | 257,831 | 0.1821 |
| 2020-12-12 | 323,307 | 147,237 | 287,609 | 0.1241 |
| 2022-01-29 | 387,963 | 164,065 | 360,386 | 0.0765 |
| 2020-12-19 | 336,489 | 156,504 | 315,047 | 0.0681 |
| 2024-01-06 | 113,172 | 55,274 | 108,740 | 0.0408 |
| 2021-01-09 | 382,218 | 182,225 | 380,145 | 0.0055 |
| 2021-01-02 | 360,564 | 173,733 | 359,386 | 0.0033 |

### RSV — 16 anomalous weeks

| Date | Actual Admissions | Expected (yhat) | Upper Bound | Anomaly Score |
|------|-------------------|-----------------|-------------|---------------|
| 2024-11-09 | 7,809 | 321 | 1,333 | 4.8592 |
| 2024-11-16 | 10,326 | 471 | 2,778 | 2.7170 |
| 2024-11-23 | 13,551 | 670 | 4,242 | 2.1945 |
| 2024-11-02 | 2,934 | 265 | 960 | 2.0571 |
| 2024-11-30 | 17,475 | 930 | 5,976 | 1.9240 |
| 2024-12-07 | 20,997 | 1,255 | 8,073 | 1.6008 |
| 2024-12-14 | 25,947 | 1,645 | 10,387 | 1.4981 |
| 2024-12-21 | 31,917 | 2,129 | 13,162 | 1.4249 |
| 2025-01-04 | 47,775 | 3,410 | 20,048 | 1.3830 |
| 2024-12-28 | 36,462 | 2,727 | 16,501 | 1.2097 |

*(6 additional lower-scoring RSV anomalies omitted; full results in `fct_anomalies_weekly`)*

---

## Data Quality

- **dbt tests:** 5/5 PASS (not_null × 4, unique × 1; 0 warnings, 0 errors)
- **Records ingested:** 294 (from existing DuckDB data; see note below)
- **Date range covered:** 2020-08-08 to 2026-03-21
- **Anomaly detection method:** Rolling 52-week baseline (mean ± 2 SD) — Prophet/Stan unavailable (CmdStan requires network access; outbound blocked by environment policy)
- **dbt models materialized:** `stg_nhsn_hrd` (view), `fct_respiratory_weekly` (table) — both rebuilt successfully
- **Anomaly table:** `fct_anomalies_weekly` — 678 rows written (281 + 281 + 116 weeks per disease)

> **Note on data ingestion:** The CDC NHSN API (`data.cdc.gov`) returned HTTP 403 (host not in network allowlist) in this execution environment. The pipeline ran against the existing `fct_respiratory_weekly` table (last ingested through 2026-03-21). A synthetic parquet file was reconstructed from the materialized DuckDB table to allow dbt to re-validate the full transformation chain. No new external data was fetched this run.