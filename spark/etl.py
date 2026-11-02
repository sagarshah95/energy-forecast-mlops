"""Optional PySpark batch example. Run after installing the spark extra.

Week 4: this is a DAILY aggregation, not a port of hourly lag features.
groupBy shuffles by (region_id, date). overwrite replaces the whole output path —
unsafe in production without a run_id partition (Week 5/15).
"""
import argparse
from pyspark.sql import SparkSession, functions as F


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/demand.parquet")
    parser.add_argument("--output", default="data/spark/daily")
    args = parser.parse_args()
    spark = SparkSession.builder.appName("EnergyDailyETL").getOrCreate()
    df = spark.read.parquet(args.input)
    # Lazy until write: Catalyst plans groupBy + agg; explain() after a lab run.
    daily = (df.withColumn("date", F.to_date("timestamp"))
             .groupBy("region_id", "date")
             .agg(F.avg("demand_mw").alias("avg_demand_mw"),
                  F.max("demand_mw").alias("peak_demand_mw")))
    daily.write.mode("overwrite").parquet(args.output)
    spark.stop()


if __name__ == "__main__":
    main()
