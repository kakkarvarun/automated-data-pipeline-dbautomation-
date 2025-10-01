# scripts/load_trips_chicago.py
import os, argparse, time, psutil
import pandas as pd, mysql.connector
from dotenv import load_dotenv
import numpy as np

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--sample", action="store_true",
    help="Load the small CI sample instead of the big local CSV")
parser.add_argument("--chunksize", type=int, default=100000,
    help="CSV chunk size (big file). CI will override to a small value")
args = parser.parse_args()

csv_path = ("data/samples/chicago_trips_sample.csv"
            if args.sample else os.getenv("TRIPS_CSV", "data/chicago_taxi_2019_01.csv"))

cfg = dict(
    host=os.getenv("MYSQL_HOST","127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT","3306")),
    user=os.getenv("MYSQL_USER","automation"),
    password=os.getenv("MYSQL_PASSWORD","pass"),
    database=os.getenv("MYSQL_DB","companydb"),
)

# Input->DB mapping (starter columns)
mapping = {
    # CSV header -------------------------> DB column
    "Trip ID": "trip_id",
    "Trip Start Timestamp": "trip_start_timestamp",
    "Trip End Timestamp": "trip_end_timestamp",
    "Trip Seconds": "trip_seconds",
    "Trip Miles": "trip_miles",
    "Pickup Census Tract": "pickup_census_tract",
    "Dropoff Census Tract": "dropoff_census_tract",
    "Pickup Community Area": "pickup_community_area",
    "Dropoff Community Area": "dropoff_community_area",
    "Fare": "fare",
    "Tips": "tips",
    "Tolls": "tolls",
    "Extras": "extras",
    "Trip Total": "trip_total",
    "Payment Type": "payment_type",
    "Company": "company",
    "Pickup Centroid Latitude": "pickup_latitude",
    "Pickup Centroid Longitude": "pickup_longitude",
    "Dropoff Centroid Latitude": "dropoff_latitude",
    "Dropoff Centroid Longitude": "dropoff_longitude",
}

def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    # Datetime columns (most Chicago files are 'YYYY-MM-DD HH:MM:SS')
    for col in ["trip_start_timestamp", "trip_end_timestamp"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="%Y-%m-%d %H:%M:%S")
            # convert to Python datetime for mysql-connector
            df[col] = df[col].apply(lambda x: x.to_pydatetime() if pd.notna(x) else None)


    # Numeric coercion
    numeric_cols = [
        "trip_seconds","trip_miles","pickup_census_tract","dropoff_census_tract",
        "pickup_community_area","dropoff_community_area","fare","tips","tolls","extras","trip_total",
        "pickup_latitude","pickup_longitude","dropoff_latitude","dropoff_longitude"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Strip strings
    for col in ["payment_type","company"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


cn = mysql.connector.connect(**cfg)
cur = cn.cursor()

chunksize = (2000 if args.sample else args.chunksize)
total = 0
t0 = time.time()
proc = psutil.Process()

insert_sql = """
INSERT INTO trips_chicago
(trip_id, trip_start_timestamp, trip_end_timestamp, trip_seconds, trip_miles,
 pickup_census_tract, dropoff_census_tract, pickup_community_area, dropoff_community_area,
 fare, tips, tolls, extras, trip_total, payment_type, company,
 pickup_latitude, pickup_longitude, dropoff_latitude, dropoff_longitude)
VALUES
(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
  trip_id = VALUES(trip_id)  -- idempotent: do nothing on duplicates
"""

# Stream CSV in chunks
for i, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunksize), start=1):
    chunk.columns = [c.strip() for c in chunk.columns]

    df = chunk.rename(columns=mapping)
    df = df[[c for c in mapping.values() if c in df.columns]]
    df = coerce_types(df)
    # ⬇️ add these two lines right HERE
    df.replace({np.nan: None}, inplace=True)  # convert float NaN to None (NULL)
    df = df.where(pd.notnull(df), None)       # also handles pandas NA/NaT robustly
    df = df.dropna(subset=["trip_id"])  # essential key (keep this after the replace)

    rows = df.reindex(columns=list(mapping.values())).values.tolist()
    if not rows:
        continue

    cur.executemany(insert_sql, rows)
    cn.commit()

    total += len(rows)
    elapsed = time.time() - t0
    rps = total / elapsed if elapsed > 0 else 0
    mem_mb = proc.memory_info().rss / (1024*1024)
    cpu = psutil.cpu_percent(interval=0.1)
    print(f"[Chunk {i}] inserted so far={total:,}  elapsed={elapsed:,.1f}s  ~{rps:,.1f} rows/s  mem={mem_mb:.1f}MB  cpu={cpu:.0f}%")

# Verify counts + aggregates
cur.execute("SELECT COUNT(*) FROM trips_chicago;")
count = cur.fetchone()[0]
print("Row count (total table):", count)

cur.execute("SELECT MIN(trip_start_timestamp), MAX(trip_end_timestamp) FROM trips_chicago;")
print("Date range:", cur.fetchone())

cur.execute("SELECT ROUND(AVG(fare),2), ROUND(AVG(trip_miles),2) FROM trips_chicago;")
print("Avg fare, miles:", cur.fetchone())

cur.close(); cn.close()
print(f"Done. Total processed this run: {total:,}")
