import os, argparse, pandas as pd, mysql.connector
from dotenv import load_dotenv

load_dotenv()
parser = argparse.ArgumentParser()
parser.add_argument("--sample", action="store_true", help="Load the small CI sample instead of the big local CSV")
args = parser.parse_args()

csv_path = "data/samples/chicago_trips_sample.csv" if args.sample else os.getenv("TRIPS_CSV", "data/chicago_taxi_2019_01.csv")

cfg = dict(
    host=os.getenv("MYSQL_HOST","127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT","3306")),
    user=os.getenv("MYSQL_USER","automation"),
    password=os.getenv("MYSQL_PASSWORD","pass"),
    database=os.getenv("MYSQL_DB","companydb"),
)

# Map raw Chicago Taxi Trips columns -> DB columns
mapping = {
    "trip_id": "trip_id",
    "trip_start_timestamp": "trip_start_timestamp",
    "trip_end_timestamp": "trip_end_timestamp",
    "trip_seconds": "trip_seconds",
    "trip_miles": "trip_miles",
    "pickup_census_tract": "pickup_census_tract",
    "dropoff_census_tract": "dropoff_census_tract",
    "pickup_community_area": "pickup_community_area",
    "dropoff_community_area": "dropoff_community_area",
    "fare": "fare",
    "tips": "tips",
    "tolls": "tolls",
    "extras": "extras",
    "trip_total": "trip_total",
    "payment_type": "payment_type",
    "company": "company",
    "pickup_latitude": "pickup_latitude",
    "pickup_longitude": "pickup_longitude",
    "dropoff_latitude": "dropoff_latitude",
    "dropoff_longitude": "dropoff_longitude"
}

def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    # datetimes
    for col in ["trip_start_timestamp","trip_end_timestamp"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    # numeric coercion
    numeric_cols = ["trip_seconds","trip_miles","pickup_census_tract","dropoff_census_tract",
                    "pickup_community_area","dropoff_community_area","fare","tips","tolls","extras","trip_total",
                    "pickup_latitude","pickup_longitude","dropoff_latitude","dropoff_longitude"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

cn = mysql.connector.connect(**cfg)
cur = cn.cursor()

chunksize = 100000 if not args.sample else 2000
total = 0

# Read CSV; sample file uses the mapped headers already
for chunk in pd.read_csv(csv_path, chunksize=chunksize):
    # Ensure all columns exist; if not, rename where possible
    cols = list(mapping.values())
    # If trip_id is missing, synthesize a surrogate
    if "trip_id" not in chunk.columns:
        chunk.insert(0, "trip_id", range(total+1, total+1+len(chunk)))

    # If raw uses same labels, fine; otherwise rename here (for real portal exports adjust as needed)
    # chunk = chunk.rename(columns=mapping)  # sample already aligned

    chunk = coerce_types(chunk)

    cols = ["trip_id","trip_start_timestamp","trip_end_timestamp","trip_seconds","trip_miles",
            "pickup_census_tract","dropoff_census_tract","pickup_community_area","dropoff_community_area",
            "fare","tips","tolls","extras","trip_total","payment_type","company",
            "pickup_latitude","pickup_longitude","dropoff_latitude","dropoff_longitude"]

    # Align order and convert NaN->None
    insert_chunk = chunk.reindex(columns=cols)
    insert_chunk = insert_chunk.where(pd.notnull(insert_chunk), None)

    rows = insert_chunk.values.tolist()
    if not rows:
        continue

    cur.executemany("""
        INSERT INTO trips_chicago (trip_id, trip_start_timestamp, trip_end_timestamp, trip_seconds, trip_miles,
          pickup_census_tract, dropoff_census_tract, pickup_community_area, dropoff_community_area,
          fare, tips, tolls, extras, trip_total, payment_type, company,
          pickup_latitude, pickup_longitude, dropoff_latitude, dropoff_longitude)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows)
    cn.commit()
    total += len(rows)
    print(f"Inserted rows: {total}")

cur.close(); cn.close()
print(f"Done. Total inserted: {total}")