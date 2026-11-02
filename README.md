# Energy Forecast MLOps — executable reference platform

**Current working release:** local one-hour-ahead electricity demand forecasting on deterministic **synthetic** data. Includes data validation, Parquet feature engineering, chronological evaluation, seasonal-naive baseline, MLflow optional tracking, FastAPI serving, tests, Docker, CI, plus optional Spark/Airflow/AWS scaffolds.

**Important:** This repository is a runnable **vertical slice**, not a claim that all 24 weeks of production features have already been implemented. Real utility data, point-in-time weather forecast vintages, 24-hour-ahead forecasting, production IAM/authentication, SageMaker serving, feature stores, Terraform beyond S3, and drift automation are future extensions. See `docs/24_WEEK_PLAN.md`.

## Architecture

```text
Synthetic generator or contract-compatible CSV
                |
         Data validation
                |
       Lag/rolling features
                |
       Parquet + manifest
                |
    Chronological 80/20 split
                |
     Naive baseline + HGBR
                |
     Metrics + joblib model ---- optional MLflow run
                |
       FastAPI /predict
                |
       Delayed-label monitoring demo
```

## Prerequisites

- Python 3.11; Git. Docker optional. Windows PowerShell, macOS and Linux supported.
- No cloud account or credentials needed for the core workflow.
- AWS resources cost money: only run Terraform when you understand billing and IAM.

## Setup

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

PowerShell may require `python -m pip install -e ".[dev]"` (double quotes).

## Run the entire local workflow

```bash
energy-ml pipeline --days 365
energy-ml train
python -m pytest -v
python -m ruff check src tests
```

Generated files:

```text
data/raw/demand.parquet
 data/processed/features.parquet
 data/manifest.json
 artifacts/model.joblib
 artifacts/metrics.json
```

Expected raw rows: **8760**; feature rows: **8592**. Model scores vary only if dependencies or implementation change; read actual values from `artifacts/metrics.json`. If model MAE is worse than baseline, report it rather than claiming improvement.

### Start the API

```bash
uvicorn energy_ml.api:app --host 127.0.0.1 --port 8000
```

In another terminal (same environment):

```bash
python scripts/smoke_test.py
```

API docs: open `http://127.0.0.1:8000/docs` in a browser. `/health` checks the process; `/ready` checks the model file. `/predict` accepts the seven numeric features from `src/energy_ml/features.py` and returns `predicted_demand_mw` plus `horizon_hours=1`. This service assumes upstream feature computation. **Do not expose publicly without authentication, request limits, TLS, and audit controls.**

### Run with Docker

First run `energy-ml pipeline` and `energy-ml train` on the host; the Docker build copies the model artifact.

```bash
docker compose up --build
```

Then run `python scripts/smoke_test.py` on the host. To stop: `docker compose down`.

### MLflow experiment tracking

```bash
# MLflow defaults to local file-based tracking unless MLFLOW_TRACKING_URI is set.
energy-ml train --mlflow
mlflow ui --port 5000
```

Open `http://127.0.0.1:5000`. Do not expose the tracking server publicly without access controls.

### Import your own CSV

```bash
energy-ml pipeline --input-csv path/to/data.csv
```

Required columns: `timestamp` (parseable datetime, interpreted as UTC if naive), `region_id`, `temperature_c`, `demand_mw`. Exactly one row per hour per region, no missing hours inside each region, no duplicates, nonnegative demand, finite numeric values. Input is assumed already normalized to MW. Real EIA files need a custom mapping adapter and may not include weather.

### Optional PySpark

Install Java compatible with your selected Spark release, then:

```bash
python -m pip install -e '.[spark]'
python spark/etl.py --input data/raw/demand.parquet --output data/spark/daily
```

### Optional Airflow

Airflow has strict version-specific Python constraints and a separate environment is strongly recommended. Install using the official Airflow constraints for your Python version, install this project in that environment, and point `AIRFLOW__CORE__DAGS_FOLDER` to `orchestration/airflow_dags`. The DAG calls local pipeline and training functions; configure shared persistent storage and MLflow backend before using distributed workers. This is a demonstration, not a hardened retraining deployment.

### Optional AWS Terraform S3 foundation

Requires AWS CLI credentials with permissions, Terraform >=1.6, and a globally unique bucket name. **Do not run without cost/security review.**

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with unique bucket_name
terraform init
terraform plan
terraform apply
# To avoid ongoing charges, empty bucket then terraform destroy
```

Only the private encrypted versioned S3 bucket is provisioned. The Lambda handler is an illustrative scaffold and is not deployed by this Terraform configuration. SageMaker resources are not provisioned.

## Evaluation and data leakage

Target timestamp `t` is the **hour being predicted**. `demand_lag_1h` uses observation `t-1`; rolling statistics exclude `t`. The model is trained using the first 80% of timestamps and evaluated on the last 20% (single-region). This assumes historical observations are published before the next hour; actual publication delays require stricter feature availability. The generator's temperature column is deliberately **not used as a feature** because it represents observed, not as-of forecast weather. No claim of 24-hour-ahead accuracy is made.

## Debugging

- `ModuleNotFoundError`: run `python -m pip install -e '.[dev]'` from repository root.
- `FileNotFoundError` in `/ready`: train model before starting the API or set `ENERGY_MODEL_PATH`.
- `Need at least 169`: increase `--days` (10 days is enough).
- Spark Java gateway failure: install compatible JDK and check `JAVA_HOME`.
- Docker `COPY artifacts/model.joblib` failure: run local training before building.
- API `422`: request must contain every field in `ForecastInput`.
- Airflow import failure: use its dedicated environment and official constraints.

## Design limitations and next steps

1. One-hour-ahead only; extend to 24 horizons with explicit forecast origin and lead time.
2. Synthetic demand; integrate EIA demand and historical weather forecast **vintages**, not realized future weather.
3. Single region for chronological training; multi-region training requires date-based group split.
4. Joblib model artifacts are pickle-based; load only artifacts from trusted build pipelines.
5. No model promotion/rollback gates, authentication, persistent feature store or managed serving yet.
6. Add structured tracing, drift tests, cost dashboards, and deployment approvals in later weeks.

See `docs/FILE_GUIDE.md` for a rationale for **every file**, `docs/24_WEEK_PLAN.md` for the sprint sequence, and `docs/24_WEEK_STUDY_GUIDE.md` for detailed weekly study material mapped to this codebase.
