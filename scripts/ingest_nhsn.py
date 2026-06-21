"""Ingest CDC NHSN Weekly Hospital Respiratory Data into a dated parquet file."""

from pathlib import Path
from datetime import datetime
import httpx
import pandas as pd

RAW_DIR = Path(__file__).parent.parent / 'data' / 'raw' / 'nhsn_hrd'
RAW_DIR.mkdir(parents=True, exist_ok=True)

CDC_NHSN_URL = 'https://data.cdc.gov/resource/ua7e-t2fy.json'
COLUMNS = [
    'weekendingdate', 'jurisdiction', 'respseason',
    'totalconfflunewadm', 'totalconffluhosppats', 'totalconffluicupats',
    'totalconfc19newadm', 'totalconfc19hosppats', 'totalconfc19icupats',
    'totalconfrsvnewadm', 'totalconfflunewadmper100k', 'totalconfc19newadmper100k',
    'totalconfflunewadmcumulativeseasonalsum', 'totalconfc19newadmcumulativeseasonalsum',
    'totalconfrsvnewadmcumulativeseasonalsum', 'numinptbeds', 'numinptbedsocc', 'pctinptbedsocc',
]

for old in RAW_DIR.glob('*.parquet'):
    old.unlink()

limit, offset, records = 5000, 0, []
while True:
    r = httpx.get(
        CDC_NHSN_URL,
        params={'$limit': limit, '$offset': offset, '$order': 'weekendingdate DESC'},
        timeout=60,
    )
    r.raise_for_status()
    batch = r.json()
    if not batch:
        break
    records.extend(batch)
    offset += limit
    print(f'Fetched {offset} records...')
    if offset >= 100_000:
        break

df = pd.DataFrame(records)
existing = [c for c in COLUMNS if c in df.columns]
df = df[existing].copy()
df['_ingested_at'] = datetime.utcnow().isoformat()

ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
out = RAW_DIR / f'nhsn_hrd_{ts}.parquet'
df.to_parquet(out, index=False)
print(f'Ingested {len(df)} records -> {out}')
