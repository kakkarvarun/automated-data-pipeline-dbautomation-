import os, glob, mysql.connector
from dotenv import load_dotenv

load_dotenv()
cfg = dict(
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    user=os.getenv("MYSQL_USER", "automation"),
    password=os.getenv("MYSQL_PASSWORD", "pass"),
    database=os.getenv("MYSQL_DB", "companydb"),
)

def main():
    cn = mysql.connector.connect(**cfg)
    cn.autocommit = False
    cur = cn.cursor()
    try:
        # Ensure schema_version exists
        cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
          id INT PRIMARY KEY AUTO_INCREMENT,
          version VARCHAR(32) NOT NULL UNIQUE,
          applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        cn.commit()

        def applied(version:str)->bool:
            cur.execute("SELECT 1 FROM schema_version WHERE version=%s", (version,))
            return cur.fetchone() is not None

        for path in sorted(glob.glob("sql/migrations/*.sql")):
            version = os.path.basename(path).split("_", 1)[0]
            if applied(version):
                print(f"[SKIP] {path}")
                continue
            print(f"[APPLY] {path}")
            with open(path, "r", encoding="utf-8") as f:
                sql = f.read()
            # naive splitter; sufficient for our simple migrations
            stmts = [s.strip() for s in sql.split(";") if s.strip()]
            for stmt in stmts:
                cur.execute(stmt)
            cur.execute("INSERT INTO schema_version(version) VALUES(%s)", (version,))
            cn.commit()
        print("All migrations applied.")
    except Exception as e:
        cn.rollback()
        print("Migration failed:", e)
        raise
    finally:
        cur.close(); cn.close()

if __name__ == "__main__":
    main()