# 24-week study guide (codebase-linked)

This guide is the detailed companion to [`docs/24_WEEK_PLAN.md`](24_WEEK_PLAN.md). Every week maps concepts to files in this repository, then tells you what to study, what to run, and what this vertical slice **does not** implement yet.

**Working release today:** one-hour-ahead demand forecast on deterministic synthetic data. See [`README.md`](../README.md) for the architecture diagram and honest limitations.

**How to use this document**

- Follow the cadence in the plan: 4h concept, 4h guided coding, 4h implementation, 4h debug/review, 4h docs/quiz/commit.
- Read the listed source files **before** extending them. Trace data through generate → validate → features → parquet → train → API.
- After each week, write a short README note: what you changed, how you reproduced it, and one failure-case test you added.
- Do not claim 24-hour-ahead accuracy, real EIA weather vintages, SageMaker serving, or a feature store until those sprints exist.
- Interview prompts include **model answers** you can say in an interview. Cover the question first, then check the answer. Appendix C has full quiz solutions.

---

## Map: plan week → primary files

| Weeks | Theme | Start here |
|---|---|---|
| 1 | Python architecture | `pyproject.toml`, `src/energy_ml/cli.py`, `src/energy_ml/generate.py`, `src/energy_ml/validation.py`, `src/energy_ml/features.py`, `tests/test_core.py` |
| 2 | SQL / contracts | `src/energy_ml/validation.py`, `sql/features.sql`, `src/energy_ml/features.py` |
| 3 | Pandas ETL / storage | `src/energy_ml/pipeline.py`, `src/energy_ml/ingest.py`, `.gitignore` |
| 4–5 | Spark | `spark/etl.py`, `pyproject.toml` `[spark]` extra |
| 6 | AWS foundation | `infrastructure/terraform/main.tf`, `.env.example`, `aws/lambda_ingest/handler.py` |
| 7–10 | Forecasting design, sklearn, evaluation, features | `src/energy_ml/features.py`, `src/energy_ml/train.py`, `tests/test_core.py` (`test_no_future_leakage`) |
| 11 | Neural nets | `pyproject.toml` `[torch]` extra (not used in core training yet) |
| 12–13 | MLflow / registry | `src/energy_ml/train.py` (`track_mlflow`), `src/energy_ml/cli.py` `--mlflow` |
| 14–15 | Airflow / hardening | `orchestration/airflow_dags/energy_training.py`, `src/energy_ml/pipeline.py` |
| 16–17 | FastAPI / Docker | `src/energy_ml/api.py`, `tests/test_api.py`, `scripts/smoke_test.py`, `Dockerfile`, `docker-compose.yml` |
| 18 | CI/CD | `.github/workflows/ci.yml` |
| 19 | SageMaker | **not in repo**; contrast with local `train.py` + Docker serving |
| 20–21 | Monitoring | `src/energy_ml/monitor.py`, `scripts/monitor_demo.py`, `src/energy_ml/api.py` health/ready |
| 22 | Retrain / rollout | Airflow DAG + `train.py` + `api.py` model path; **no champion/challenger yet** |
| 23–24 | Design, security, portfolio | `README.md`, `docs/FILE_GUIDE.md`, Terraform public-access block, `.gitignore` |

---

## Shared weekly ritual

Run this from the repo root after you install `python -m pip install -e ".[dev]"`:

```bash
energy-ml pipeline --days 365
energy-ml train
python -m pytest -v
python -m ruff check src tests
```

Expected from the README: **8760** raw rows and **8592** feature rows for 365 days (8760 − 168 lag warmup). Scores live in `artifacts/metrics.json`; never hard-code “the model always beats naive.”

---

# Stage 1 — Weeks 1–6: data pipeline (local, no secrets)

**Gate:** pipeline reproducible locally; no secrets in Git; schema checks pass.

---

## Week 1: Python architecture

### Concepts

- **src layout vs flat scripts.** `pyproject.toml` uses `[tool.setuptools.packages.find] where = ["src"]` and a console script `energy-ml = "energy_ml.cli:main"`. Installing with `pip install -e .` puts `src/` on the import path so tests and CLI share one package.
- **Typing and contracts.** `ingest.py` uses `str | Path`. `validation.py` raises a dedicated `DataValidationError(ValueError)` instead of a generic exception.
- **Logging vs print.** `pipeline.py` logs the manifest; `cli.py` configures `logging.basicConfig` then prints JSON for automation.
- **Determinism.** `generate.py` uses `numpy.random.default_rng(seed)` so tests can assert frame equality.

### Codebase walkthrough

1. `pyproject.toml` — runtime deps (pandas, sklearn, fastapi, mlflow) vs optional extras (`dev`, `spark`, `airflow`, `torch`, `aws`). Python `>=3.11`.
2. `src/energy_ml/__init__.py` — package version `0.1.0`.
3. `src/energy_ml/cli.py` — argparse subcommands `pipeline` and `train`; no business logic in the CLI.
4. `src/energy_ml/generate.py` — synthetic UTC hourly series: diurnal demand, weekend offset, temperature-driven load, Gaussian noise.
5. `src/energy_ml/validation.py` — required columns, TZ-aware timestamps, finite numerics, non-negative demand, unique `(region_id, timestamp)`, hourly continuity per region.
6. `src/energy_ml/features.py` — `FEATURES` list is the single source of truth for training and API schema.
7. `tests/test_core.py` — `test_deterministic`, `test_contract`, `test_missing_hour`, `test_no_future_leakage`, `test_end_to_end`.

### Hands-on

- Trace `energy-ml pipeline --days 10` from `cli.main` → `run_pipeline` → generate/validate/features.
- Add a new failure-case test (for example duplicate timestamps or `NaN` temperature) in `tests/test_core.py`.
- Sketch a module diagram: CLI must not import sklearn if you later split serving.

### Interview prompts and answers

**Why src layout instead of putting modules at the repo root?**  
Installable packages should not put the project root on `sys.path`. A root-level `energy_ml.py` or `tests/` sitting next to scripts can shadow installed packages and make `import energy_ml` pick up an accidental local file. `pyproject.toml` sets `packages.find where = ["src"]` and `energy-ml = "energy_ml.cli:main"`, so editable install (`pip install -e .`) is the only supported import path for CLI, tests, Airflow tasks, and the API.

**Why a custom `DataValidationError` rather than `assert`?**  
`assert` is for internal programmer mistakes and can be stripped with `python -O`. Bad data is an expected operational failure. `DataValidationError(ValueError)` in `validation.py` is catchable, has a clear message (`Negative demand`, `Missing or irregular hours`), and is what `test_contract` / `test_missing_hour` assert with `pytest.raises`. Pipelines can fail the job without looking like a crashed assertion.

**How would you make the generator timezone-naive by mistake, and which test would catch it?**  
Change `pd.date_range(..., tz="UTC")` in `generate.py` to a naive range. `validate_demand` requires `DatetimeTZDtype` and raises `timestamp must be timezone-aware datetime`. `test_contract` calls `validate_demand` on generated data, so it would fail. `ingest_csv` would still coerce CSV timestamps with `utc=True`, which is a second path you should not rely on for the generator.

### Not in this week’s slice

Packaging a wheel to PyPI, structured JSON logging, and a real EIA adapter.

---

## Week 2: SQL and data contracts

### Concepts

- **Contract first.** Incoming CSV must already match `timestamp`, `region_id`, `temperature_c`, `demand_mw` (`ingest.py` comment and `validate_demand`).
- **Window functions vs Pandas.** `sql/features.sql` is the warehouse equivalent of `build_features`: `LAG(..., 1/24/168)` and `AVG(...) ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING`.
- **Timestamp integrity.** Validation requires timezone-aware datetime and exact 1-hour diffs. Naive timestamps are coerced to UTC only at CSV ingest (`pd.to_datetime(..., utc=True)`).

### Codebase walkthrough

Compare these two implementations line by line:

- Pandas: `src/energy_ml/features.py` (`shift`, `shift(1).rolling(24).mean()`).
- SQL: `sql/features.sql` (`WINDOW w AS (PARTITION BY region_id ORDER BY timestamp)`).

The rolling window **excludes the current row** in both (SQL `1 PRECEDING`; Pandas `shift(1)` before `rolling`). That is the leakage-control rule.

### Hands-on

- Load `data/raw/demand.parquet` into local PostgreSQL (or DuckDB) and run `sql/features.sql` against a table named `electricity_demand`.
- Compare a few rows to `data/processed/features.parquet`.
- Write a SQL test that fails if any hour gap exists (`LEAD(timestamp) - timestamp != interval '1 hour'`).
- Capture `EXPLAIN ANALYZE` for the window query; note sort/window nodes.

### Interview prompts and answers

**Why `PARTITION BY region_id`?**  
Lags and rolling means are properties of one region's time series. Without the partition, `LAG(demand_mw, 1)` could pull the previous row from another region after a sort. Pandas does the same with `groupby("region_id")` before `shift`. `sql/features.sql` uses `WINDOW w AS (PARTITION BY region_id ORDER BY timestamp)`.

**Why UTC everywhere?**  
Hourly continuity (`Timedelta(hours=1)`) breaks across DST if you use a local zone: a fall-back night has two 1:00s or a skipped hour. The generator emits UTC; ingest parses with `utc=True`. Energy markets also settle on a defined standard time; storing UTC and converting only at display time avoids silent duplicate keys.

**What index would you add for `(region_id, timestamp)` and why is uniqueness part of the contract, not just an index?**  
A unique btree on `(region_id, timestamp)` speeds point lookups and the window `ORDER BY timestamp` within a region. An index does not by itself reject bad files before they land. `validate_demand` checks `duplicated(["region_id", "timestamp"])` so training never sees two demands for the same hour. The database constraint is defense in depth; the Python contract is the pipeline gate.

### Not in this week’s slice

A live warehouse, dbt project, or CDC from a utility SCADA system.

---

## Week 3: Pandas ETL and storage

### Concepts

- **Vectorization.** Generator and features use NumPy/Pandas ops, not Python row loops (except `groupby` over regions).
- **Parquet.** `_write_parquet_atomic` writes `.tmp.parquet` then `Path.replace` so readers never see a half-written file on the same filesystem.
- **Manifest.** `data/manifest.json` records row counts, source (`synthetic:seed=42` or CSV path), and `forecast_horizon_hours: 1`.
- **Git hygiene.** `.gitignore` excludes `data/`, `artifacts/`, `.env`, Terraform state.

### Codebase walkthrough

- `src/energy_ml/pipeline.py` — orchestration only: ingest or generate, validate, engineer, write, return manifest.
- `src/energy_ml/ingest.py` — thin adapter; **you** must map real files onto the contract.
- `tests/test_core.py` `test_end_to_end` — 30 days → `720 - 168` feature rows.

### Hands-on

- Time `run_pipeline` for 30 vs 365 vs 1095 days; record wall clock in a short ETL note.
- Break atomic replace (write directly to the final path, kill mid-write) and describe the failure mode.
- Add a data-quality report dict to the manifest (min/max demand, missingness after features). Keep it JSON.

### Interview prompts and answers

**Why Parquet over CSV for `data/processed`?**  
Parquet keeps dtypes (timezone-aware timestamps, floats) without re-parsing, is columnar (you read `FEATURES` without the raw temperature column if you choose), and compresses well. CSV would round-trip timestamps as strings and invite `ingest` bugs. Training reads `data/processed/features.parquet` via `pandas.read_parquet`.

**When is `replace()` not atomic (cross-device copies)?**  
`Path.replace` is atomic on the same filesystem. If `path` is on another mount (for example writing tmp on local disk then replacing a path on NFS/S3FS), the replace becomes copy+delete and readers can see a partial file. `_write_parquet_atomic` in `pipeline.py` writes `*.tmp.parquet` next to the destination assuming a local disk. Object storage needs a different pattern (write a new key, then update the manifest pointer).

**Why ignore `data/` in Git but still commit `sql/` and `src/`?**  
`data/` is generated, large, and reproducible from `generate_demand(seed=42)` or an external CSV. Committing it duplicates artifacts and hides whether the pipeline still runs. `sql/` and `src/` are the specification. `.gitignore` also drops `artifacts/`, `.env`, and Terraform state for the same reason: regenerate or keep secrets out of history.

---

## Week 4: PySpark fundamentals

### Concepts

- Lazy execution: transformations (`withColumn`, `groupBy`) vs action (`write`).
- Partitioning: output path `data/spark/daily` is a directory of Parquet files.
- Catalyst: after a run, inspect the physical plan (`daily.explain()`).

### Codebase walkthrough

`spark/etl.py` is a **daily aggregation**, not a port of lag features:

- Read `data/raw/demand.parquet`.
- `to_date(timestamp)`, group by `region_id, date`.
- `avg` and `max` demand; `mode("overwrite").parquet`.

Optional extra: `pyproject.toml` `[project.optional-dependencies] spark`.

### Hands-on

- Install a compatible JDK, then `python -m pip install -e ".[spark]"` and run the job after a local pipeline.
- Add `explain(True)` (or `explain("formatted")`) and save the plan as a lab artifact.
- **Sprint extension:** port `build_features` to Spark window functions (`Window.partitionBy("region_id").orderBy("timestamp")`) and compare counts to Pandas (8592 rows for 365 days).

### Interview prompts and answers

**Why is this job not the training feature pipeline?**  
`spark/etl.py` aggregates to **daily** `avg_demand_mw` and `peak_demand_mw`. Training needs **hourly** lags (1/24/168) and a rolling mean that excludes the current hour (`features.py`). Daily peaks cannot reconstruct hour-level supervised rows. The Spark job is a scale-out ETL example, not a substitute for `build_features`.

**What shuffle happens in `groupBy`?**  
`groupBy("region_id", "date")` requires all rows for a key on the same partition, so Spark shuffles by hash of those columns. The later `write.parquet` can shuffle again depending on partitioning. For this tiny file the cost is small; on skewed keys it dominates (Week 5).

**Why overwrite mode for a demo, and why is that dangerous in production without partitioning by run_id?**  
`mode("overwrite")` replaces the entire `data/spark/daily` directory so reruns are easy locally. In production a failed job can wipe good data, and two overlapping runs can clobber each other. Safer pattern: write to `.../run_id=<id>/` (immutable) and point a `_SUCCESS` or manifest at the latest good run.

---

## Week 5: Advanced Spark

### Concepts

Skew, broadcast joins, cache vs checkpoint, partition count vs file count, AQE.

### What exists vs what you build

The repo only has the small daily aggregation. This week is **your** performance lab on top of `spark/etl.py`.

### Hands-on

- Scale synthetic data (`generate_demand` for multiple regions or more days), write partitioned Parquet (`partitionBy("region_id")`).
- Compare runtime: unpartitioned read vs partition prune.
- Introduce an artificial skew (one region 100× rows), measure stage time, then salting or two-phase aggregate.
- Write a one-page comparison: Pandas pipeline vs Spark daily job vs Spark feature job (if you built it).

### Interview prompts and answers

**When would you not use Spark for this dataset (8760 rows)?**  
Spark's JVM, shuffle, and task scheduling overhead dwarf a 8k-row Pandas job. Use Spark when data no longer fits memory, you need cluster I/O to a lake, or the same job must run in a warehouse/Spark shop for operational consistency. This repo's core path is Pandas by design; Spark is an optional extra.

**Checkpoint vs cache for iterative algorithms?**  
`cache`/`persist` keeps a DataFrame in memory (or memory+disk) but the lineage stays: a lost executor recomputes from the original scan. `checkpoint` truncates lineage by writing to reliable storage and creating a new RDD/DataFrame root. Use cache for reuse inside one job; checkpoint when lineage is long (iterative ML, many unions) or you need a recovery cut. Neither is used in `spark/etl.py` today.

---

## Week 6: AWS foundation

### Concepts

Least-privilege IAM, private buckets, encryption at rest, versioning, no secrets in Git, cost of idle resources.

### Codebase walkthrough

- `infrastructure/terraform/main.tf` — S3 bucket + versioning + AES256 SSE + **all four** public access blocks. Variables: `aws_region`, `bucket_name`.
- `infrastructure/terraform/terraform.tfvars.example` — placeholder name; copy to `terraform.tfvars` (gitignored via `*.tfstate*` and you should not commit real names if they encode account IDs).
- `.env.example` — `AWS_REGION`, `ENERGY_S3_BUCKET`; real `.env` is gitignored.
- `aws/lambda_ingest/handler.py` — logs S3 event bucket/key only; **not** wired in Terraform.

### Hands-on (only after a cost/IAM review)

- `terraform init && terraform plan` with a globally unique bucket name.
- Draw the diagram: producer → S3 (private, versioned, encrypted) → future Lambda/EventBridge. Label what Terraform actually creates today (bucket only).
- Estimate monthly cost of an empty versioned bucket vs storing Parquet + request volume.

### Interview prompts and answers

**Why block public ACLs and public policies?**  
S3 has two ways to go public: object ACLs and bucket policies. `aws_s3_bucket_public_access_block` sets `block_public_acls`, `ignore_public_acls`, `block_public_policy`, and `restrict_public_buckets` so a mistaken `ACL=public-read` or `Principal: "*"` cannot expose demand data. Encryption and versioning do not replace this.

**Why is the Lambda handler a scaffold rather than `aws_lambda_function` in this Terraform?**  
`aws/lambda_ingest/handler.py` only logs bucket/key. Wiring Lambda means IAM roles, event notifications, packaging, CloudWatch logs, and a billable function even when idle. The README states Terraform provisions **only** the private versioned encrypted bucket. That keeps Week 6 scoped to IAM/S3/cost, not a half-deployed ingest path.

**How do you destroy without leaving a non-empty bucket bill?**  
Versioned buckets cannot be deleted until all versions (including delete markers) are gone. Empty the bucket (including versions), then `terraform destroy`. Leaving objects or an abandoned bucket accrues storage cost. Never apply in an account you cannot clean up.

---

# Stage 2 — Weeks 7–13: leakage-safe modeling

**Gate:** leakage-safe horizon-aware backtesting; model beats seasonal-naive on holdout **or** you document why not.

---

## Week 7: Forecasting problem design

### Concepts

- **Target time `t`:** the hour being predicted. In this repo, `target_demand_mw = demand_mw` at `t`.
- **Forecast origin:** implicitly `t-1` for a 1-hour horizon (you observe demand at `t-1` before predicting `t`).
- **As-of features:** lags and rolling stats must not use demand at `t` or later.
- **Weather availability:** `generate.py` creates `temperature_c` at the same timestamp as demand. README forbids using it as a feature because it is **observed**, not a forecast vintage.

### Codebase walkthrough

- `src/energy_ml/features.py` — lags 1, 24, 168; rolling mean uses `shift(1)` then 24-hour window; `dropna` drops the 168-hour warmup.
- `tests/test_core.py` `test_no_future_leakage` — after timestamp 200, add 10000 MW to future demand; features at `t <= cutoff` must be unchanged.
- `src/energy_ml/pipeline.py` manifest field `forecast_horizon_hours: 1`.
- `src/energy_ml/api.py` response also returns `"horizon_hours": 1`.

### Hands-on

- Draw a timeline: origin, horizon, which columns are known at origin.
- Design (do not fake completion of) 1–24h labels: for horizon `h`, target is `demand_mw.shift(-h)` and features must still be computed at origin.
- Add a test: mutating demand at `t` must not change features whose target is `t` (already true for lags; prove it for rolling mean).

### Interview prompts and answers

**What breaks if weather forecasts are replaced by realized temperature?**  
At forecast origin `t-1` you do not know the true temperature at `t` (or at `t+h` for longer horizons). Using `temperature_c` from `generate.py` would leak the simultaneous observation that is generated with demand (`14 * abs(temperature - 21)`). Offline metrics would look strong and production would miss that weather because only a **forecast vintage** issued before origin is legal. That is why `FEATURES` omits temperature.

**Why is a single chronological 80/20 split invalid for multi-region data?**  
`train.py` does `iloc[:split]` after sorting timestamps. With two regions, rows interleave: the last 20% of **rows** can still include early dates of a second region, and train/test **times** can overlap. The code raises if `train["timestamp"].max() >= test["timestamp"].min()`. Multi-region needs a **date** cutoff applied to all regions (or group-aware split), not a row fraction.

---

## Week 8: Scikit-learn baselines

### Concepts

Seasonal naive (yesterday same hour), pipelines, tree vs linear models, `random_state` for reproducibility.

### Codebase walkthrough

`src/energy_ml/train.py`:

- Sort by timestamp; 80/20 **row** split; abort if `train.timestamp.max() >= test.timestamp.min()`.
- Model: `HistGradientBoostingRegressor(max_iter=150, learning_rate=0.07, random_state=42)`.
- Baseline: `test["demand_lag_24h"]` — seasonal naive for hourly data with daily seasonality.
- Metrics: MAE and RMSE for model and baseline (`sklearn.metrics.mean_absolute_error`, `root_mean_squared_error`).
- Artifact: `joblib.dump({"model", "features", "metrics"})` — pickle; load only trusted files (README + `api.py` docstring).

### Hands-on

- Train and record `artifacts/metrics.json`. If model MAE > baseline MAE, document it; do not tune until you have a scorecard.
- Add a second baseline (lag-168 weekly naive) to the metrics dict.
- Optional: wrap HGBR in `sklearn.pipeline.Pipeline` even if there is no scaler (trees do not need one; a linear model would).

### Interview prompts and answers

**Why HistGradientBoosting over a default `GradientBoostingRegressor` on this size?**  
HGBR bins features and grows trees on histograms; it is the sklearn implementation meant for larger tabular data and is faster with similar accuracy. For 8k rows either works; HGBR is the production-shaped choice and matches common “gradient boosting, not a neural net” interview answers. `random_state=42` plus generator seed keeps runs comparable. A linear model would need scaling; trees do not.

**Why store `features` next to the model?**  
`joblib.dump({"model", "features", "metrics"})` pins column order. `/predict` builds `DataFrame([record], columns=bundle["features"])`. If someone retrains with a new column and the API still sends the old payload, you want a mismatch you can detect, not silently shuffled columns. The list in `features.py` is the training contract; the bundle is the serving contract.

---

## Week 9: Evaluation

### Concepts

MAE vs RMSE (outlier sensitivity), WAPE, peak-hour error, walk-forward / rolling origin vs one split.

### What exists

One chronological holdout in `train.py`. No WAPE, no peak-hour slice, no rolling-origin loop.

### Hands-on

- Write a notebook or script that, for several cut dates, trains on all rows `< cutoff` and tests the next 7 days.
- Compute MAE overall, MAE for hours 16–20 (peak), and WAPE = `sum(|e|) / sum(|y|)`.
- Error analysis: residual vs hour, vs day_of_week, vs demand level. Save plots outside Git (`data/` is ignored; use `docs/` only for committed figures you intend to publish).

### Interview prompts and answers

**Why RMSE can rank models differently from MAE on peak errors?**  
MAE treats every MW of error equally. RMSE squares errors, so a few peak-hour misses dominate. A model that is slightly worse on typical hours but much better on peaks can win RMSE and lose MAE, or the reverse. Grid operators often care about peaks; that is why Week 9 adds peak-hour MAE, not only the overall numbers in `metrics.json`.

**Why delayed labels matter before you trust a dashboard?**  
`evaluate_recent` needs `actual` and `predicted` of equal length. Demand at hour `t` is not known at origin `t-1`; scoring must wait until the observation is published. A dashboard that “scores” using a proxy (or realized weather) will not match production. Week 21’s monitor is explicitly **offline delayed-label** MAE vs a holdout `reference_mae`.

---

## Week 10: Feature engineering

### Concepts

Cyclical encoding (`hour_sin`/`hour_cos` so hour 23 is close to 0), calendar, holidays, weather **forecasts**, feature store vs a Parquet file.

### Codebase walkthrough

`FEATURES` in `features.py`:

```text
demand_lag_1h, demand_lag_24h, demand_lag_168h,
rolling_mean_24h, hour_sin, hour_cos, day_of_week
```

API `ForecastInput` in `api.py` **must stay aligned** with this list. Smoke test reads the last feature row and posts those keys (`scripts/smoke_test.py`).

### Hands-on

- Document lineage: generator field → validation rule → feature formula → model input → API field.
- Add `is_weekend` **or** keep `day_of_week`; justify redundancy.
- Do **not** add `temperature_c` until you have as-of forecast files.
- Sketch a feature-store table: `feature_name, entity_id, event_timestamp, value, as_of_timestamp`.

### Interview prompts and answers

**Why sin/cos instead of one-hot hour?**  
One-hot hour is 24 sparse columns and treats hour 23 and hour 0 as unrelated. `hour_sin` / `hour_cos` map the clock onto a circle (`2 * pi * hour / 24` in `features.py`) so those hours are close in feature space, with two continuous inputs trees can split on. `day_of_week` stays numeric 0–6; a production model might still one-hot weekday if splits on integers are awkward.

**What happens if API schema and `FEATURES` drift?**  
If the client omits a field, Pydantic returns **422** (`test_input_validation` uses negative `demand_lag_1h`). If both sides add different fields but JSON still validates, `DataFrame([record], columns=bundle["features"])` reindexes to the **bundle** order and can insert NaNs or drop extras—bad, but better than pandas aligning by insertion order incorrectly. The smoke test reads `FEATURES` from the package, which only helps if API and package stay in sync. Registry signatures (Week 12–13) are the real fix.

---

## Week 11: PyTorch and TensorFlow

### Concepts

Tensors, autograd, DataLoader, train/val split, overfitting on small series.

### What exists

`pyproject.toml` extra `torch = ["torch>=2.3,<3"]`. Core training is sklearn only. No Keras example in-tree.

### Hands-on

- Keep sklearn as champion. Train a small MLP on the same `FEATURES` and same split; log MAE next to HGBR.
- Regularize (weight decay, early stopping). Compare parameter count vs 8592 rows.
- Write a tradeoff memo: latency, artifact format, explainability, ops complexity vs HGBR + joblib.

### Interview prompts and answers

**Why might a neural net lose to seasonal naive on strong daily seasonality?**  
`demand_lag_24h` is already an excellent predictor when the series is strongly diurnal (the generator uses a sine on hour). An MLP on seven features, with 8592 rows and no inductive bias for seasonality, can overfit noise (`rng.normal` in `generate.py`) and lose to “same hour yesterday.” That is a valid outcome: document it in the tradeoff memo; do not force a neural story.

**How would a sequence model change leakage rules?**  
An LSTM/TFT lookback window must end at the forecast origin, not include target-hour demand or future weather. Padding, teacher forcing, and decoder horizon steps are easy leakage sources. You would still need a test like `test_no_future_leakage`: mutate demand after cutoff and assert encoder inputs at origin are unchanged. Multi-horizon output does not license using `t+1` actuals as if they were known.

---

## Week 12: MLflow tracking

### Concepts

Experiment vs run, params/metrics/artifacts, model signature, tracking URI.

### Codebase walkthrough

`train_model(..., track_mlflow=False)`:

- `mlflow.set_experiment("energy-demand-forecasting")`
- logs `max_iter`, `learning_rate`
- logs MAE/RMSE keys (skips `*_rows`)
- `mlflow.sklearn.log_model(model, name="energy-model")`

CLI: `energy-ml train --mlflow`. README: local file store unless `MLFLOW_TRACKING_URI` is set. `.env.example` has `ENERGY_MLFLOW_URI=sqlite:///mlflow.db`. `.gitignore` includes `mlruns/` and `mlflow.db`.

### Hands-on

- Run two trainings with different `max_iter`; compare in `mlflow ui --port 5000`.
- Log `FEATURES` as a param or artifact JSON.
- Add an input example / signature so serving and training columns cannot silently diverge.

### Interview prompts and answers

**File store vs tracking server vs managed MLflow?**  
Default MLflow uses `./mlruns` (gitignored). Fine for one laptop. A tracking server plus artifact store (S3) lets multiple workers log without clobbering local files; Airflow workers need that (README). Managed MLflow (Databricks, SageMaker experiments, etc.) adds IAM, backup, and access control you do not have to run. `.env.example` shows `ENERGY_MLFLOW_URI=sqlite:///mlflow.db` as a middle step—still single-host.

**Why not expose the UI publicly?**  
The UI can show params, metrics, and often model artifacts (pickle). Unauthenticated access is model theft and a pickle RCE path if anyone can download and you load blindly. README: do not expose the tracking server without access controls. Same rule as FastAPI.

---

## Week 13: Model registry

### Concepts

Registered model versions, aliases (`champion` / `challenger`), approval, rollback, loading by alias not by filename.

### What exists

A single `artifacts/model.joblib` overwritten every train. API loads `ENERGY_MODEL_PATH` (default that file) via `lru_cache`. **No registry, no aliases.**

### Hands-on

- After `--mlflow`, register the sklearn model in the Tracking UI or via API; assign alias `champion`.
- Write a **model release checklist**: metrics vs baseline, leakage tests green, artifact hash, who approved, how to revert (`ENERGY_MODEL_PATH` to previous joblib).
- Note pickle risk: never load models from untrusted uploads.

### Interview prompts and answers

**File path vs registry alias for production?**  
Today serving loads `ENERGY_MODEL_PATH` (default `artifacts/model.joblib`). Paths are simple and work in Docker (`/app/artifacts/model.joblib`). They do not record who approved the model, and overwrite has no history except S3 versioning if you upload there. A registry alias (`champion`) lets you roll back by moving the alias, not by remembering a filename. This repo has tracking (`log_model`) but **no** registered aliases yet.

**What happens to `get_bundle` cache if you swap the file without restarting?**  
`get_bundle` is `@lru_cache(maxsize=1)`. The first successful load is reused for the process lifetime. Replacing the file on disk does nothing until you restart workers or call `get_bundle.cache_clear()`. A “deploy” that only copies a new joblib into the container without recycle will keep scoring with the old model. Call this out in the Week 22 runbook.

---

# Stage 3 — Weeks 14–18: orchestrate, serve, ship

**Gate:** orchestrated, containerized service; integration tests and a rollback plan.

---

## Week 14: Airflow orchestration

### Concepts

DAG, schedule, catchup, retries, backfill, idempotency, task boundaries.

### Codebase walkthrough

`orchestration/airflow_dags/energy_training.py`:

- Airflow 3 Task SDK: `@dag` / `@task`.
- `schedule="@weekly"`, `catchup=False`, `max_active_runs=1`.
- `prepare` → `run_pipeline(days=365)`; `train` → `train_model(track_mlflow=True)`.
- Functions imported **inside** tasks to keep DAG parse light.

README warns: separate env + official constraints; this is not a hardened retrain deployment.

### Hands-on

- Split into three DAGs conceptually: ingest/validate, forecast/serve batch, retrain. Implement locally if Airflow is installed.
- Add retries and a data-interval based output path so reruns do not clobber blindly (today `data/` is a fixed directory — **not idempotent across dates**).
- Document why `catchup=False` for a synthetic generator.

### Interview prompts and answers

**Idempotency: what should `run_pipeline` do if Monday’s Parquet already exists?**  
Today it always regenerates and atomically replaces `data/raw/demand.parquet` and `features.parquet`. That is idempotent **only** in the sense that a retry ends in the same synthetic seed=42 output. For real dated data, a retry should write `run_id` outputs or skip if the manifest for that data interval already matches the source hash. Blind replace of a shared `data/` path is not safe with two Airflow runs.

**Why `max_active_runs=1`?**  
The DAG writes fixed paths and a single `model.joblib`. Two overlapping weekly runs would race on Parquet and artifacts. `catchup=False` avoids a storm of backfills against the generator. Production should still use unique output keys so you can raise `max_active_runs` later.

---

## Week 15: MLOps pipeline hardening

### Concepts

Run IDs, manifests, lineage, retries, poison-message handling, artifact immutability.

### Codebase walkthrough

Already present:

- Manifest JSON (row counts, source, paths, horizon).
- Atomic Parquet replace.
- Fail-fast validation.
- CI runs pipeline + train + pytest + ruff.

Gaps: no `run_id` in paths, no schema version field, no recovery from mid-train failure beyond “run again.”

### Hands-on

- Add `run_id` (UTC timestamp or UUID) to manifest and optionally to artifact filenames.
- Demo: delete `features.parquet`, rerun pipeline, confirm train succeeds.
- Demo: corrupt a CSV (negative demand), show `DataValidationError` stops the job.

### Interview prompts and answers

**Why fail fast rather than drop bad rows silently?**  
Dropping a missing hour would hide a SCADA gap and train across a fabricated continuity. `validate_demand` raises on nulls, negatives, duplicates, and irregular hours so the job stops and the manifest is not updated as success. Silent row drops change `feature_rows` (expected 8760−168) without anyone noticing.

**How would you resume Spark overwrite safely with run_id partitions?**  
Write `s3://bucket/daily/run_id=<uuid>/`. Never overwrite the previous run_id. On success, update `manifest.json` (or a `latest` pointer) to that run_id. A retry starts a new run_id; failed folders can be garbage-collected later. `mode("overwrite")` on a shared path is the anti-pattern from Week 4.

---

## Week 16: FastAPI serving

### Concepts

Pydantic v2 models, 422 vs 503, liveness vs readiness, trusted artifact loading.

### Codebase walkthrough

`src/energy_ml/api.py`:

- `ForecastInput` constraints: lags ≥ 0, sin/cos in [-1, 1], `day_of_week` 0–6.
- `/health` — process up.
- `/ready` — model file loadable; 503 otherwise.
- `/predict` — same 503 if missing model; builds one-row DataFrame in **bundle feature order**.
- `get_bundle` is `lru_cache(maxsize=1)`.

Tests: `tests/test_api.py` health + negative lag → 422.  
Client: `scripts/smoke_test.py` (needs a running server and `data/processed/features.parquet`).

### Hands-on

- Start uvicorn; hit `/health`, `/ready` before and after training.
- Add an integration test that trains into `tmp_path`, sets `ENERGY_MODEL_PATH`, and posts a valid payload (TestClient can still miss env/cache issues — consider cache_clear).
- Document the contract: this API does **not** accept raw timestamps; upstream must compute features.

### Interview prompts and answers

**Why 503 on missing model instead of 500?**  
500 means the handler crashed. 503 means the service is up but **not ready** to take traffic—exactly what `/ready` and `/predict` do on `FileNotFoundError`/`OSError`. Load balancers should stop sending to a replica that fails readiness, while `/health` can still return 200 so the process is not killed as “dead.” `test_api.py` does not cover 503; a good extra test would.

**Why not load the model at import time?**  
Import-time `joblib.load` would crash `uvicorn` (and `from energy_ml.api import app` in tests) whenever the file is missing. Tests import `app` without a model (`test_health`, `test_input_validation`). Lazy load in `get_bundle` lets the process start, serve `/health`, and fail `/ready` until `energy-ml train` has run.

---

## Week 17: Docker and serving performance

### Concepts

Image layers, copying artifacts, non-root user, port binding, load tests, p95 latency.

### Codebase walkthrough

`Dockerfile`:

- `python:3.11-slim`
- Copy `pyproject.toml`, `README.md`, `src/`; `pip install .`
- `useradd -m appuser` then copy `artifacts/model.joblib` then `USER appuser`
- `CMD uvicorn ... --host 0.0.0.0 --port 8000`

`docker-compose.yml` sets `ENERGY_MODEL_PATH=/app/artifacts/model.joblib` and `restart: unless-stopped`.

**Build requires a host-trained model** (CI trains; local Docker build fails if `COPY artifacts/model.joblib` missing — README debugging section).

### Hands-on

- `docker compose up --build` then `python scripts/smoke_test.py`.
- Note: image is **not** multi-stage; list that as a hardening task (smaller runtime, no gcc if you add compile deps).
- Benchmark with a simple loop or `hey`/`wrk` against `/predict`; record p50/p95. Single worker uvicorn is not production scale.

### Interview prompts and answers

**Why non-root?**  
`useradd -m appuser` then `USER appuser` so a compromised uvicorn cannot write system files as root. The model file must be readable by that user (copied before the USER switch in this Dockerfile). This is a baseline CIS/container hygiene control, not full isolation.

**Why copy the model after `pip install`?**  
`COPY pyproject.toml README.md src` then `pip install` is a cacheable dependency layer. `COPY artifacts/model.joblib` comes later so retraining does not bust the pip layer. Downside: the build **fails** if you never trained on the host (README debugging). Multi-stage builds would copy only the installed package + model into a slimmer runtime image; this Dockerfile is single-stage.

**Host `0.0.0.0` in Docker vs `127.0.0.1` in README?**  
Inside a container, binding `127.0.0.1` is only the container loopback; published ports would not reach uvicorn. `0.0.0.0:8000` is required for `docker-compose` `ports: "8000:8000"`. On a developer laptop, README uses `127.0.0.1` so the API is not advertised on the LAN. Neither setup includes auth.

---

## Week 18: CI/CD

### Concepts

GitHub Actions, reproducible Python, lint/test as gates, deploying without long-lived AWS keys (OIDC — **not configured here**).

### Codebase walkthrough

`.github/workflows/ci.yml`:

- `on: push` and `pull_request`
- Python 3.11
- `pip install -e '.[dev]'`
- `pytest -q`
- `python -m energy_ml.cli pipeline --days 30` then `train`
- `ruff check src tests`

No deploy job, no OIDC, no image publish.

### Hands-on

- Push a branch and confirm the workflow.
- Add a job artifact upload for `artifacts/metrics.json` (optional).
- Design (on paper) a deploy workflow: build image, push to ECR, update ECS/Lambda, using OIDC. Do not store AWS keys in the repo.

### Interview prompts and answers

**Why run pipeline+train in CI if unit tests already call `test_end_to_end`?**  
`test_end_to_end` imports `run_pipeline` / `train_model` with `tmp_path`. CI also runs `python -m energy_ml.cli pipeline --days 30` and `train`, which verifies the **console script / module entrypoint**, default relative `data/` and `artifacts/` paths, and that packaging in the Actions runner works. `ruff check src tests` is extra and not in pytest. Duplication is cheap compared to a broken CLI.

**Difference between linting in CI and pre-commit hooks?**  
Pre-commit is optional and local; it prevents bad commits if installed. CI is the merge gate that runs even if a contributor skipped hooks. This repo has ruff in CI (`.github/workflows/ci.yml`) and no pre-commit config. Both should use the same `ruff` version from `.[dev]`.

---

# Stage 4 — Weeks 19–24: cloud, monitor, operate, tell the story

**Gate:** AWS deployment, monitoring, retraining gates, cost controls, architecture demo — **most of this is still a sprint target**, not a completed product.

---

## Week 19: SageMaker

### Concepts

Managed training jobs, channels, instance cost, model.tar.gz, batch transform vs endpoints, IAM execution roles.

### What exists

Local `train.py` + Docker FastAPI. Terraform does **not** create SageMaker resources (README).

### Hands-on

- Map current code to SageMaker: entry point would call `train_model`; data channel ≈ `data/processed/features.parquet`; output ≈ `model.joblib`.
- Cost sketch: `ml.m5.large` hours vs local CPU for this tiny dataset (answer should be: SageMaker is for the **operating model**, not for 8k rows).
- If you run a job, use a tiny instance, tear it down, and record the bill.

### Interview prompts and answers

**Batch transform vs real-time endpoint for hourly forecasts?**  
A 1-hour-ahead (or 24-hour-ahead) forecast is naturally a **batch** job just after each hour’s data lands: transform a feature file, write predictions. A real-time endpoint is for interactive `/predict` or sub-minute requests. SageMaker batch transform bills for job runtime; an endpoint bills while the instance sits idle. For this problem, batch + this repo’s Docker API for demos is the honest split. Do not imply SageMaker is provisioned; Terraform does not create it.

**How do you keep the same FEATURES contract inside a SageMaker container?**  
Ship the same `energy_ml` package as the training/inference image, persist `features` inside the model tar (as `train.py` already does in joblib), and validate incoming rows against that list. Do not reimplement columns in a notebook cell that only exists in SageMaker. The entry point should call `train_model` / the same `FEATURES` import.

---

## Week 20: Cloud monitoring

### Concepts

Liveness vs readiness vs latency SLOs, structured logs, CloudWatch metrics/alarms, cardinality.

### What exists

- API `/health` and `/ready`
- `pipeline.py` `LOG.info("Pipeline completed: %s", manifest)`
- Lambda handler `logger.info("New object bucket=%s key=%s", ...)`
- No CloudWatch dashboard, no X-Ray, no p95 instrumentation

### Hands-on

- Add request timing middleware in FastAPI (log method, path, status, ms). Do not log raw payloads if they could become sensitive later.
- Define alerts: 5xx rate, `/ready` failing, p95 `/predict` > threshold.
- Draw which metrics live in the app vs the load balancer vs the host.

### Interview prompts and answers

**Why `/health` can be green while `/ready` is 503?**  
`/health` only returns `{"status": "ok"}` — the process answers HTTP. `/ready` calls `get_bundle()` and returns 503 if `ENERGY_MODEL_PATH` is missing. Kubernetes/load balancers should use readiness to drain traffic and liveness only to restart a wedged process. Restarting a replica because the model file is not mounted yet makes the outage worse.

**Alert fatigue: what should not page a human?**  
Do not page on a single 422 (bad client), on generator-scale MAE noise below `reference_mae * 1.25`, or on `/health` probes. Page on sustained 5xx, `/ready` failing across replicas, p95 `/predict` above SLO, or `performance_alert` persisting after delayed labels for a full peak window. `monitor.py` already uses a 25% tolerance to avoid flapping on four demo points.

---

## Week 21: Model monitoring

### Concepts

Label delay (you cannot score hour `t` until demand at `t` is published), drift vs performance, thresholds, PSI/KS vs MAE regression.

### Codebase walkthrough

`src/energy_ml/monitor.py` `evaluate_recent`:

- Nonempty equal-length arrays, finite values
- MAE vs `reference_mae * tolerance` (default 1.25)
- Returns `performance_alert` bool

`scripts/monitor_demo.py` uses four fake points and `reference_mae=20.0`.

This is **offline delayed-label monitoring**, not live drift on features.

### Hands-on

- Wire `reference_mae` from `artifacts/metrics.json` `model_mae`.
- Simulate a regime shift (add +200 MW to actuals) and show the alert flips.
- Design a drift report: distribution of `demand_lag_1h` this week vs train set. Do not alert on one hour of noise.

### Interview prompts and answers

**Why compare to a reference MAE from the holdout, not zero?**  
The model is not expected to have zero error; synthetic noise is ~30 MW sd and baseline MAE is whatever `metrics.json` reports. Alerting on MAE > 0 is always on. `evaluate_recent(..., reference_mae, tolerance=1.25)` flags **regression** versus the score you accepted at train time. Wire `reference_mae` from `model_mae` in `artifacts/metrics.json`.

**How does publication delay change the monitoring DAG?**  
Schedule monitoring after the actual for hour `t` is available (often t+something, not t+1 minute). The Airflow forecast DAG can emit predictions immediately; the monitor task should depend on a sensor or a later data interval. Scoring too early either skips rows (`len` mismatch → `ValueError`) or uses incomplete actuals.

---

## Week 22: Retraining and rollout

### Concepts

Triggers (calendar, performance alert, data volume), champion/challenger, canary, automatic rollback.

### What exists

Weekly Airflow DAG that retrains and overwrites artifacts. API caches one bundle. No comparison gate, no canary traffic split.

### Hands-on

- Write a release runbook:
  1. Train challenger on new data.
  2. Require `model_mae < baseline_mae` (or documented exception) and leakage tests.
  3. Swap `ENERGY_MODEL_PATH` or registry alias.
  4. Restart workers to clear `lru_cache`.
  5. Rollback by pointing at the previous joblib.
- Implement a **guard** in code: refuse to overwrite `model.joblib` if challenger MAE is worse than current `metrics.json` unless `--force`.

### Interview prompts and answers

**Why weekly retrain on synthetic data is theater unless data distribution changes?**  
`generate_demand(seed=42)` is the same distribution every run. Retraining weekly will produce essentially the same HGBR. A calendar trigger is still useful as an **operational rehearsal** (DAG, artifact promotion, rollback). A real trigger is new EIA data, a `performance_alert`, or a schema change. Say this in interviews so you are not claiming automated learning from noise.

**Canary for a batch-hourly forecast vs a high-QPS endpoint?**  
For hourly batch, “canary” means score the challenger **offline** on the last delayed-label window (and leakage tests) before swapping `ENERGY_MODEL_PATH` / alias; maybe write both predictions for a week. Traffic-splitting 5% of HTTP requests matters for high-QPS APIs, not for one prediction per region per hour. Rollback is “point at the previous joblib and restart to clear `lru_cache`.”

---

## Week 23: System design and security

### Concepts

Availability, throughput, cost, IAM, threat model (pickle RCE, public API, public S3, secrets in Git).

### Codebase walkthrough (security-relevant)

- `.gitignore`: `.env`, `*.tfstate*`, `artifacts/`, credentials patterns.
- Terraform: encryption, versioning, public access block.
- README: do not expose API without auth, rate limits, TLS, audit.
- `api.py`: load only trusted artifacts (joblib/pickle).
- Dockerfile: non-root user.
- No authentication on FastAPI (by design of the slice).

### Hands-on

- Write 2–3 architecture decision records (ADRs) in `docs/adr/` if you want them in Git, for example:
  - 1-hour horizon first vs 24-hour
  - sklearn HGBR vs neural net
  - local joblib vs SageMaker endpoint
- Threat model table: asset, threat, mitigation, residual risk.
- Scale sketch: single region hourly vs 1000 feeders at 5-minute resolution.

### Interview prompts and answers

**Walk through the architecture diagram in README and name every honesty caveat.**  
Generator or contract CSV → validate → lag/rolling features → Parquet/manifest → chronological 80/20 → naive + HGBR → metrics/joblib → optional MLflow → FastAPI `/predict` → delayed-label monitor. Caveats you must say: synthetic not EIA; 1-hour horizon not 24; temperature unused because it is observed; single region; joblib pickle trust; no auth; Terraform is S3 only; Spark/Airflow/Lambda/SageMaker/feature store/drift automation are scaffolds or absent; if model MAE > baseline, report it.

**Where would you put auth (API Gateway vs app middleware)?**  
For AWS, API Gateway (or an ALB + OIDC) terminates TLS, issues keys/JWT, and rate-limits before traffic hits uvicorn. App-level middleware is a second check and is what you would add to FastAPI for local Docker. Putting auth only in the app and binding `0.0.0.0` without a gateway is easier to misconfigure. This slice has **neither**; README forbids public expose.

---

## Week 24: Portfolio polish and interviews

### Concepts

Evidence over claims, STAR stories, reproducible demo, known limitations.

### Codebase walkthrough

Commit these as the spine of the demo:

1. `README.md` — setup, commands, limitations.
2. `docs/FILE_GUIDE.md` — why each file exists.
3. `docs/24_WEEK_PLAN.md` — curriculum.
4. This study guide — proof you can teach the system.
5. Tests as evidence of leakage control and contracts.

### Demo script (10–12 minutes)

1. Show generator is synthetic and seeded (`generate.py`).
2. Run pipeline; open `manifest.json`.
3. Show `test_no_future_leakage`.
4. Train; open `metrics.json`; compare to naive.
5. Hit `/health`, `/ready`, `/predict`.
6. Show Docker and CI files.
7. Show Terraform bucket policy intent.
8. Close with the README “not yet” list.

### STAR narrative bank (use real commands you ran)

**Leakage**  
- Situation: One-hour-ahead demand model; rolling stats can leak the target.  
- Task: Prove features at time t do not use demand after t.  
- Action: `shift(1).rolling(24)` plus `test_no_future_leakage`, which adds 10000 MW after a cutoff and asserts earlier feature rows are unchanged.  
- Result: Cutoff features match; the test fails if you drop the `shift(1)`.

**Contracts**  
- Situation: CSV/synthetic data can contain negatives or gaps.  
- Task: Keep bad data out of Parquet/training.  
- Action: `validate_demand` + `test_contract` / `test_missing_hour`.  
- Result: `DataValidationError` stops the pipeline; no silent drops.

**Serving**  
- Situation: API may start before `energy-ml train`.  
- Task: Orchestrators must distinguish “process up” from “can score.”  
- Action: `/health` 200 vs `/ready` 503; Pydantic 422 on `demand_lag_1h < 0`.  
- Result: Smoke test only after train; Docker copies `model.joblib`.

**Honesty**  
- Situation: Portfolio pressure to over-claim.  
- Task: Describe the system accurately.  
- Action: README limitations + this guide’s “not in this week’s slice.”  
- Result: Interviewers hear 1-hour synthetic vertical slice, not fake 24h SageMaker.

**Optional spoken answers (30 seconds)**  
“I built a leakage-safe 1h demand slice: UTC hourly contract, lag/rolling features, HGBR vs day-ago naive, joblib + FastAPI with readiness, tests in CI, optional Spark/Airflow/S3. I did not use realized temperature as a feature, and I do not claim 24-hour-ahead or production IAM.”

### Portfolio v1.0 checklist

- [ ] Clean README with limitations
- [ ] Green `pytest` and ruff locally
- [ ] `metrics.json` from a recorded run
- [ ] API smoke test screenshot or logged JSON
- [ ] CI badge or workflow screenshot
- [ ] This study guide used as interview notes
- [ ] No secrets, no claimed unbuilt features

---

## Appendix A — Data flow (implemented)

```text
generate_demand() or ingest_csv()
        │
        ▼
validate_demand()          # DataValidationError
        │
        ▼
build_features()           # dropna on 168h warmup
        │
        ▼
Parquet + manifest.json    # atomic write
        │
        ▼
train_model()              # 80/20 chronological, HGBR vs lag-24
        │
        ├─ artifacts/model.joblib
        ├─ artifacts/metrics.json
        └─ optional MLflow run
        │
        ▼
FastAPI /predict           # Pydantic ForecastInput
        │
        ▼
evaluate_recent()          # delayed-label MAE vs reference
```

## Appendix B — Row-count arithmetic

For `days = D` and one region:

- Raw hours = `D * 24`
- Feature rows = `D * 24 - 168` (longest lag)
- Week 1 README example: `D = 365` → 8760 raw, 8592 features
- `test_end_to_end`: `D = 30` → 720 − 168 = 552 feature rows

## Appendix C — Quiz and full answers

Try the questions first, then read the answers.

1. Which function forbids using current-hour demand in the 24h rolling mean?
2. Which test would fail if you used `rolling(24).mean()` without `shift(1)`?
3. Why is `temperature_c` generated but omitted from `FEATURES`?
4. What HTTP status does `/ready` return if `model.joblib` is missing?
5. What Terraform resources are **not** created for Lambda?
6. Why does `train.py` raise on overlapping train/test timestamps?
7. What does CI run that `test_end_to_end` already covers, and what extra does CI add?
8. Why is joblib unsafe to load from an arbitrary URL?

### Answers

1. **`build_features` in `src/energy_ml/features.py`.** It computes `g["demand_mw"].shift(1).rolling(24).mean()`, so the window is the previous 24 hours, not including target hour `t`. SQL does the same with `ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING`.

2. **`test_no_future_leakage` in `tests/test_core.py`.** Without `shift(1)`, the rolling mean at the cutoff timestamp includes demand at `t`. Adding 10000 MW to all rows after cutoff still changes the cutoff row’s own demand, so feature frames `a` and `b` would differ and `assert_frame_equal` would fail. (`test_end_to_end` would still pass; it does not check leakage.)

3. **It is observed weather at the same timestamp as demand, not a forecast issued before origin.** `generate.py` even uses temperature inside the demand formula (`14 * abs(temperature - 21)`). Training on it would leak a quantity you would not have as a vintage forecast in production. README states this explicitly.

4. **HTTP 503.** `ready()` catches `FileNotFoundError` and `OSError` from `get_bundle()` and raises `HTTPException(status_code=503)`. `/health` would still be 200. `/predict` uses the same 503 path.

5. **No Lambda is deployed.** `infrastructure/terraform/main.tf` creates the S3 bucket, versioning, AES256 encryption, and public access block. `aws/lambda_ingest/handler.py` is not referenced by an `aws_lambda_function`, IAM role, or event notification.

6. **A row-wise 80/20 split is only chronological for one sorted series.** With multiple regions, interleaved rows can put later timestamps in train and earlier ones in test (or overlap). `if train["timestamp"].max() >= test["timestamp"].min()` raises `Train/test overlap: use a date-based split for multi-region data`.

7. **Overlap:** pytest `test_end_to_end` already runs `run_pipeline` (30 days) and `train_model` in a temp dir. **Extra in CI:** `python -m energy_ml.cli pipeline --days 30` and `train` (packaged CLI, default `data/` / `artifacts/` paths on the runner) and `ruff check src tests`. Install step is `pip install -e '.[dev]'`.

8. **joblib/pickle can execute arbitrary code during load.** `api.py` says load only trusted artifacts. An attacker-supplied URL or a world-writable `artifacts/model.joblib` is a remote-code-execution path. Production should hash artifacts from CI and refuse unsigned files.

### Extra self-check (with answers)

**Expected row counts for `--days 365`?** 8760 raw (`365 * 24`), 8592 features (`8760 - 168`). For 30 days: 720 raw, 552 features (`test_end_to_end`).

**What is the seasonal naive baseline?** `test["demand_lag_24h"]` — demand at the same hour yesterday.

**What does the API accept?** The seven `FEATURES` fields, not raw `timestamp`/`demand_mw`. Upstream must run `build_features`. `horizon_hours` in the response is always `1`.

**Where do metrics live?** `artifacts/metrics.json` (`model_mae`, `model_rmse`, `baseline_mae`, `baseline_rmse`, row counts). Never memorize a “winning” MAE.

**What is gitignored that Docker still needs?** `artifacts/model.joblib`. Train on the host before `docker compose build`.

**Is MLflow required to train?** No. `--mlflow` / `track_mlflow=True` is optional. Airflow’s train task sets `track_mlflow=True`.

**Default monitoring alert rule?** `mae > reference_mae * 1.25` in `evaluate_recent`.

## Appendix D — Suggested commit messages by stage

Use these only when you actually complete the work:

- Weeks 1–3: tests for contracts, manifests, ETL notes
- Weeks 7–10: leakage tests, scorecard, feature lineage
- Weeks 14–18: DAG split, API tests, Docker/CI
- Weeks 19–24: ADRs, runbook, monitoring, portfolio evidence

Do not commit `.env`, `tfstate`, or `artifacts/model.joblib` unless you have a deliberate, documented reason (the Docker build currently **expects** a local artifact that is gitignored — produce it with `energy-ml train` before `docker compose build`).
