import os, argparse, mysql.connector
from dotenv import load_dotenv

load_dotenv()
parser = argparse.ArgumentParser()
parser.add_argument("--expect-min", type=int, default=1)
args = parser.parse_args()

cfg = dict(
    host=os.getenv("MYSQL_HOST","127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT","3306")),
    user=os.getenv("MYSQL_USER","automation"),
    password=os.getenv("MYSQL_PASSWORD","pass"),
    database=os.getenv("MYSQL_DB","companydb"),
)

cn = mysql.connector.connect(**cfg)
cur = cn.cursor()
cur.execute("SELECT COUNT(*) FROM trips_chicago;")
count = cur.fetchone()[0]
print("Row count:", count)

cur.execute("SELECT MIN(trip_start_timestamp), MAX(trip_end_timestamp) FROM trips_chicago;")
minmax = cur.fetchone()
print("Date range:", minmax)

cur.execute("SELECT AVG(fare), AVG(trip_miles) FROM trips_chicago;")
aggs = cur.fetchone()
print("Avg fare, miles:", aggs)

cur.close(); cn.close()

if count < args.expect_min:
    raise SystemExit(f"FAIL: expected at least {args.expect_min}, got {count}")
print("OK")