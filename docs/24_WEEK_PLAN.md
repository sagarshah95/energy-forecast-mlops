# 24-week, 20-hours/week mastery plan

Detailed study notes, file walkthroughs, exercises, and interview prompts: [`docs/24_WEEK_STUDY_GUIDE.md`](24_WEEK_STUDY_GUIDE.md).

## Weekly cadence
- Monday (4h): concept study and notes.
- Tuesday (4h): guided coding and unit tests.
- Wednesday (4h): implementation and integration.
- Thursday (4h): debugging, profiling, and design review.
- Friday (4h): documentation, quiz, Git commit, retrospective.

Each week: 8h building, 5h fundamentals, 3h tests/debugging, 2h documentation, 2h review.

## Week-by-week objectives

### Week 1: Python architecture
**Deep study:** Modules, packaging, typing, errors, logging, tests.
**Hands-on sprint:** Synthetic generator, validation, feature pipeline.
**Portfolio deliverable:** CLI, tests, data manifest.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 2: SQL and data contracts
**Deep study:** CTEs, window functions, indexes, timestamp integrity.
**Hands-on sprint:** Import CSV to PostgreSQL and compare SQL vs Pandas features.
**Portfolio deliverable:** SQL tests and explain plans.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 3: Pandas ETL and storage
**Deep study:** Vectorization, chunking, Parquet, partitioning.
**Hands-on sprint:** Incremental ingestion and data quality reports.
**Portfolio deliverable:** ETL benchmark.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 4: PySpark fundamentals
**Deep study:** Lazy execution, partitions, shuffles, Catalyst.
**Hands-on sprint:** Port transformations to Spark.
**Portfolio deliverable:** Spark job and execution plan.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 5: Advanced Spark
**Deep study:** Skew, joins, caching, performance, checkpoints.
**Hands-on sprint:** Scale dataset and tune Spark.
**Portfolio deliverable:** Performance comparison report.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 6: AWS foundation
**Deep study:** IAM, S3, encryption, credentials, cost controls.
**Hands-on sprint:** Deploy versioned S3 data lake with Terraform.
**Portfolio deliverable:** Infrastructure diagram and cost estimate.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 7: Forecasting problem design
**Deep study:** Forecast origin, horizon, backtesting, weather availability.
**Hands-on sprint:** Create horizon-aware labels and strict as-of features.
**Portfolio deliverable:** Leakage tests for 1–24h forecasts.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 8: Scikit-learn baselines
**Deep study:** Seasonal naive, regression, pipelines, scaling.
**Hands-on sprint:** Train and benchmark models.
**Portfolio deliverable:** Baseline scorecard.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 9: Evaluation
**Deep study:** MAE, RMSE, WAPE, peak-hour metrics, walk-forward.
**Hands-on sprint:** Rolling-origin evaluation.
**Portfolio deliverable:** Error analysis notebook/report.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 10: Feature engineering
**Deep study:** Cyclical time, holidays, weather, availability lags.
**Hands-on sprint:** Feature transformations and feature store design.
**Portfolio deliverable:** Feature lineage documentation.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 11: PyTorch and TensorFlow
**Deep study:** Tensors, autograd, dataloaders, overfitting.
**Hands-on sprint:** Train a small MLP in PyTorch; compare Keras example.
**Portfolio deliverable:** Neural baseline and tradeoff memo.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 12: MLflow tracking
**Deep study:** Runs, params, metrics, artifacts, signatures.
**Hands-on sprint:** Track multiple model experiments.
**Portfolio deliverable:** Reproducible experiment report.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 13: Model registry
**Deep study:** Versioning, approvals, aliases, rollback.
**Hands-on sprint:** Promote validated model artifact.
**Portfolio deliverable:** Model release checklist.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 14: Airflow orchestration
**Deep study:** DAGs, retries, backfills, idempotency.
**Hands-on sprint:** Separate data, forecast, retrain DAGs.
**Portfolio deliverable:** Working local Airflow workflows.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 15: MLOps pipeline hardening
**Deep study:** Data tests, lineage, artifacts, failure recovery.
**Hands-on sprint:** Add run IDs, manifests and recovery paths.
**Portfolio deliverable:** Resiliency demo.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 16: FastAPI serving
**Deep study:** Pydantic, request schemas, errors, health/readiness.
**Hands-on sprint:** Serve model with REST API.
**Portfolio deliverable:** API contract and integration tests.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 17: Docker and serving performance
**Deep study:** Images, multi-stage builds, non-root, load testing.
**Hands-on sprint:** Containerize inference and benchmark.
**Portfolio deliverable:** Container and latency report.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 18: CI/CD
**Deep study:** GitHub Actions, OIDC, secrets, artifact promotion.
**Hands-on sprint:** Automate lint/test/build/deploy gates.
**Portfolio deliverable:** Green CI and deployment workflow.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 19: SageMaker
**Deep study:** Training jobs, model packaging, batch inference, costs.
**Hands-on sprint:** Run managed training and batch prediction.
**Portfolio deliverable:** AWS inference demo.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 20: Cloud monitoring
**Deep study:** CloudWatch, structured logs, metrics, alerts.
**Hands-on sprint:** Instrument errors, throughput, p95 latency.
**Portfolio deliverable:** Monitoring dashboard.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 21: Model monitoring
**Deep study:** Drift, delayed labels, thresholds, alert fatigue.
**Hands-on sprint:** Build performance checks and drift reports.
**Portfolio deliverable:** Model health report.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 22: Retraining and rollout
**Deep study:** Triggers, champion/challenger, canary, rollback.
**Hands-on sprint:** Implement guarded retraining and rollback.
**Portfolio deliverable:** Release runbook.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 23: System design and security
**Deep study:** Availability, throughput, cost, IAM, threat modeling.
**Hands-on sprint:** Design scalable cloud architecture.
**Portfolio deliverable:** Architecture decision records.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

### Week 24: Portfolio polish and interviews
**Deep study:** Documentation, demos, tradeoffs, STAR narratives.
**Hands-on sprint:** Demo end-to-end system and publish evidence.
**Portfolio deliverable:** Portfolio release v1.0.
**Self-check:** Explain design tradeoffs, reproduce output, add a failure-case test, and record evidence in README.

## Stage gates
- Weeks 1–6: data pipeline reproducible locally; no secrets in Git; schema checks pass.
- Weeks 7–13: leakage-safe horizon-aware backtesting; model exceeds seasonal-naive baseline on held-out data or findings documented.
- Weeks 14–18: orchestrated, containerized service; integration tests and rollback plan.
- Weeks 19–24: AWS deployment, monitoring, retraining gates, cost controls, architecture demo.

## Important distinction
The included runnable reference implementation is a **one-hour-ahead, synthetic-data vertical slice**. The 24-hour horizon, real forecast-vintage weather data, production AWS serving, feature store, and neural model are future sprint implementations, not falsely claimed as completed.
