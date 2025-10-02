# PROG8850 — Assignment 2 (Chicago Taxi Trips)

Prereqs (Docker, Python)

Local run:

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
 1) start DB + create user
 2) python scripts/run_migrations.py
 3) python scripts/load_trips_chicago.py --sample    # proof
 4) python scripts/load_trips_chicago.py             # big file (set TRIPS_CSV)
 5) python scripts/backup_script.py


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