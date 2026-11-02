# File-by-file guide: purpose and rationale

Inline study comments live in the Python, SQL, Spark, Terraform, Docker, and CI files (week numbers + design rationale). Do not treat comments as a substitute for tests.

| File | What it does | Why it exists |
|---|---|---|
| `pyproject.toml` | Defines installable package and optional extras | Consistent dependencies and entry point |
| `.env.example` | Documents environment variables | No secrets committed |
| `.gitignore` | Excludes generated data, credentials and artifacts | Clean and safe repository |
| `src/energy_ml/generate.py` | Reproducible synthetic hourly observations | Testable input without API credentials |
| `src/energy_ml/ingest.py` | Reads validated CSV contract | Adapter for real datasets |
| `src/energy_ml/validation.py` | Enforces types, uniqueness, continuity | Prevents bad data from reaching training |
| `src/energy_ml/features.py` | Historical lags, rolling average, calendar encoding | Leakage-safe predictors for one-hour target |
| `src/energy_ml/pipeline.py` | Coordinates ETL and saves manifest/Parquet | Repeatable pipeline execution |
| `src/energy_ml/train.py` | Trains gradient boosting and naive benchmark | Quantifies predictive value on chronological holdout |
| `src/energy_ml/monitor.py` | Compares delayed actuals with predictions | Simple performance regression alert |
| `src/energy_ml/cli.py` | Exposes pipeline and train subcommands | Automation-friendly interface |
| `src/energy_ml/api.py` | FastAPI validation, readiness and inference | Interactive model serving |
| `tests/test_core.py` | Determinism, validation, leakage and full pipeline | Prevents regressions |
| `tests/test_api.py` | Health and request contract tests | Stable API behavior |
| `sql/features.sql` | SQL equivalent of selected features | Practice warehouse window functions |
| `spark/etl.py` | Distributed daily aggregation | Demonstrates Spark extension |
| `orchestration/airflow_dags/energy_training.py` | Weekly training DAG | Optional scheduling reference |
| `aws/lambda_ingest/handler.py` | Handles S3 event metadata | Event-driven ingestion scaffold |
| `infrastructure/terraform/main.tf` | Creates encrypted, private, versioned S3 bucket | Infrastructure as code foundation |
| `scripts/smoke_test.py` | Calls running API with valid feature row | End-to-end inference smoke test |
| `scripts/monitor_demo.py` | Exercises performance monitor | Demonstrates alert semantics |
| `Dockerfile` | Builds API image with model artifact | Reproducible container serving |
| `docker-compose.yml` | Runs API container locally | Simple local deployment |
| `.github/workflows/ci.yml` | Installs, tests, lints, trains | Automated integration gate |
| `docs/24_WEEK_PLAN.md` | 24-week 20-hour curriculum | Learning and sprint milestones |
| `docs/24_WEEK_STUDY_GUIDE.md` | Week-by-week study material tied to source files | Guided reading, labs, and interview prep |
| `docs/FILE_GUIDE.md` | Explains file purposes and design choices | Review and interview preparation |
| `README.md` | Setup, architecture, commands, caveats | Onboarding and portfolio presentation |
