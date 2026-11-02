"""Single CLI entry point for ingestion, training and evaluation.

Wired in pyproject.toml as ``energy-ml = "energy_ml.cli:main"``.
Keep this module free of sklearn/pandas logic so serving images can stay thin later.
"""
import argparse
import json
import logging
from energy_ml.pipeline import run_pipeline
from energy_ml.train import train_model


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Energy forecasting MLOps CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("pipeline")
    build.add_argument("--days", type=int, default=365)
    build.add_argument("--data-dir", default="data")
    build.add_argument("--input-csv")
    train = sub.add_parser("train")
    train.add_argument("--data-dir", default="data")
    train.add_argument("--artifact-dir", default="artifacts")
    train.add_argument("--mlflow", action="store_true")
    args = parser.parse_args()
    result = (run_pipeline(args.days, args.data_dir, args.input_csv)
              if args.command == "pipeline"
              else train_model(args.data_dir, args.artifact_dir, args.mlflow))
    # JSON on stdout for Airflow/CI; logs go to stderr via basicConfig.
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
