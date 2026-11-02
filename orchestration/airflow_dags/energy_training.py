"""Optional Airflow 3 DAG. Install Airflow separately using official constraints.

Week 14: weekly retrain demo. catchup=False and max_active_runs=1 because
run_pipeline writes fixed data/ paths (not idempotent by data interval).
Imports happen inside tasks so DAG parse does not load sklearn.
"""
from datetime import datetime
from airflow.sdk import dag, task


@dag(dag_id="energy_weekly_retrain", schedule="@weekly",
     start_date=datetime(2026, 1, 1), catchup=False, max_active_runs=1)
def energy_weekly_retrain():
    @task
    def prepare():
        from energy_ml.pipeline import run_pipeline
        return run_pipeline(days=365)

    @task
    def train(_manifest):
        from energy_ml.train import train_model
        return train_model(track_mlflow=True)

    train(prepare())


energy_weekly_retrain()
