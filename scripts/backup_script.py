# scripts/backup_script.py
import subprocess
from datetime import datetime
from pathlib import Path
import os, logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
load_dotenv()

def main():
    backup_dir = Path("backups"); backup_dir.mkdir(parents=True, exist_ok=True)
    keep = int(os.getenv("BACKUP_KEEP", "5"))

    # We will run mysqldump inside the container (works reliably on Windows)
    container = os.getenv("MYSQL_CONTAINER", "companydb-mysql")
    user = os.getenv("MYSQL_USER", "automation")
    pwd  = os.getenv("MYSQL_PASSWORD", "pass")
    db   = os.getenv("MYSQL_DB", "companydb")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = backup_dir / f"{db}_{ts}.sql"

    logging.info(f"Creating backup: {out.name}")
    cmd = ["docker","exec",container,"mysqldump",f"-u{user}",f"-p{pwd}",db]

    with open(out, "wb") as f:
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        logging.error(proc.stderr.decode("utf-8"))
        raise SystemExit(1)

    size_mb = out.stat().st_size / (1024*1024)
    logging.info(f"Backup complete: {out} ({size_mb:.2f} MB)")

    # Retention
    backups = sorted(backup_dir.glob(f"{db}_*.sql"))
    if len(backups) > keep:
        for p in backups[0:len(backups)-keep]:
            logging.info(f"Deleting old backup: {p.name}")
            p.unlink()

if __name__ == "__main__":
    main()
