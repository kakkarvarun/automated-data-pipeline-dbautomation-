# PROG8850 — Assignment 2 (Chicago Taxi Trips)

Automate **database schema migrations** and **CI/CD** with the City of Chicago **Taxi Trips** open dataset.
Students work **locally** for big-file ingestion and push to **GitHub** where CI runs a small sample.

## Dataset
- Source: City of Chicago Data Portal — "Taxi Trips"
- Use **one month** locally (large CSV/Parquet). For CI, use the provided tiny sample at `data/samples/chicago_trips_sample.csv`.

## Repo Structure
```
.
├─ README.md
├─ .gitignore
├─ .env.example
├─ sql/
│  ├─ migrations/
│  │  ├─ 001_create_schema_version.sql
│  │  ├─ 002_create_projects.sql
│  │  ├─ 003_add_projects_budget.sql
│  │  └─ 004_create_trips_chicago.sql
│  └─ tests/001_assert_schema.sql
├─ scripts/
│  ├─ run_migrations.py
│  ├─ load_trips_chicago.py
│  └─ verify_counts.py
├─ data/
│  └─ samples/chicago_trips_sample.csv
├─ .github/workflows/ci_cd_pipeline.yml
└─ docs/report_template.md
```

## Quick Start (Local)
1. Install MySQL 8 (or MariaDB 10.6+) and create DB/user:
   ```sql
   CREATE DATABASE companydb;
   CREATE USER 'automation'@'%' IDENTIFIED BY 'pass';
   GRANT ALL PRIVILEGES ON companydb.* TO 'automation'@'%';
   FLUSH PRIVILEGES;
   ```

2. Python env and deps:
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   pip install mysql-connector-python python-dotenv pandas
   cp .env.example .env
   ```
   - (Optional) Set `TRIPS_CSV` in `.env` to your local monthly CSV path.

3. Run migrations twice to prove idempotency:
   ```bash
   python scripts/run_migrations.py
   python scripts/run_migrations.py
   ```

4. Load data:
   - **CI-sized sample**: `python scripts/load_trips_chicago.py --sample`
   - **Full local file** (set `TRIPS_CSV` first): `python scripts/load_trips_chicago.py`

5. Verify:
   ```bash
   python scripts/verify_counts.py --expect-min 1
   ```

## GitHub CI/CD
- On push/PR, GitHub Actions starts a MySQL service, runs migrations, loads the **sample** file,
  asserts schema, and verifies counts.
- Workflow: `.github/workflows/ci_cd_pipeline.yml`

## Notes
- Do **not** commit large CSVs (`data/*.csv` is ignored except `data/samples/*`).
- Keep migrations **idempotent** and tracked in `schema_version`.
- Document results in `docs/report_template.md` (or export to PDF/DOCX).

## License
For classroom use.