"""
Pipeline Execution & Storage Orchestration Module for Flight Data Pipeline.
Manages data ingestion, cleaning, metrics computation, and partitioned storage writes.
"""

from datetime import datetime
import logging
import os
import sys

from pyspark.sql import functions as F

try:
    from flight_pipeline.clean_data import clean_flights
    from flight_pipeline.flights_stats import (
        aircraft_by_country,
        fastest_flights,
        flight_stats,
        flights_on_ground,
    )
    from flight_pipeline.ingest_flights import get_spark_session, ingest_flights
except ImportError:
    from clean_data import clean_flights
    from flights_stats import (
        aircraft_by_country,
        fastest_flights,
        flight_stats,
        flights_on_ground,
    )
    from ingest_flights import get_spark_session, ingest_flights

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

ENABLE_PARQUET = os.getenv("PIPELINE_ENABLE_PARQUET", "0") == "1"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def add_partition_columns(df):
    """Adds standard ingest_date and ingest_hour partitioning columns."""
    if df.rdd.isEmpty():
        return df

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    hour_str = datetime.utcnow().strftime("%H")

    return (
        df.withColumn("ingest_date", F.lit(today_str))
        .withColumn("ingest_hour", F.lit(hour_str))
    )


def _save_csv(df, csv_path, partition_cols=None):
    """Saves DataFrame as CSV file, creating parent directories as required."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    pdf = df.toPandas()
    pdf.to_csv(csv_path, index=False)
    logger.info("Saved CSV output: %s", csv_path)


def _save_with_fallback(df, dataset_name, partition_cols=None):
    """
    Writes DataFrame using Hive-partitioned Lakehouse layout (Parquet) with automatic fallback to CSV.

    :param df: PySpark DataFrame
    :param dataset_name: Dataset identifier (e.g. 'flights', 'stats')
    :param partition_cols: List of column names to partition output by
    """
    if partition_cols is None:
        partition_cols = ["ingest_date"]

    parquet_dir = os.path.join(OUTPUT_DIR, dataset_name)
    csv_file = os.path.join(OUTPUT_DIR, f"{dataset_name}.csv")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if ENABLE_PARQUET:
        try:
            logger.info("Writing partitioned Parquet dataset to: %s", parquet_dir)
            writer = df.write.mode("overwrite")
            if partition_cols:
                # Check partition columns exist in DataFrame
                valid_partition_cols = [c for c in partition_cols if c in df.columns]
                if valid_partition_cols:
                    writer = writer.partitionBy(*valid_partition_cols)
            writer.parquet(parquet_dir)
            logger.info("Successfully wrote Parquet dataset: %s", parquet_dir)
            return
        except Exception as exc:
            logger.warning("Parquet write failed for %s (%s). Falling back to CSV write.", parquet_dir, exc)

    # Fallback to CSV storage
    _save_csv(df, csv_file)

    # Also save inside partitioned folder for standard lake layout
    if partition_cols and "ingest_date" in df.columns:
        date_val = datetime.utcnow().strftime("%Y-%m-%d")
        partitioned_csv_dir = os.path.join(OUTPUT_DIR, dataset_name, f"ingest_date={date_val}")
        partitioned_csv_file = os.path.join(partitioned_csv_dir, f"{dataset_name}.csv")
        _save_csv(df, partitioned_csv_file)


def run_pipeline():
    """Executes the full flight data ETL pipeline."""
    logger.info("Starting Flight Data Pipeline execution...")
    spark = get_spark_session()

    # 1. Ingest
    raw_df = ingest_flights(spark=spark)

    # 2. Clean & Validate
    clean_df = clean_flights(raw_df)

    # 3. Add Partitioning Metadata
    partitioned_df = add_partition_columns(clean_df)

    # 4. Compute Metrics & Aggregates
    stats = flight_stats(partitioned_df)
    country = aircraft_by_country(partitioned_df)
    fastest = fastest_flights(partitioned_df)
    on_ground = flights_on_ground(partitioned_df)

    # 5. Persist Partitioned Datasets
    _save_with_fallback(partitioned_df, "flights", partition_cols=["ingest_date"])
    _save_with_fallback(stats, "stats", partition_cols=None)
    _save_with_fallback(country, "aircraft_by_country", partition_cols=None)
    _save_with_fallback(fastest, "fastest_flights", partition_cols=None)
    _save_with_fallback(on_ground, "flights_on_ground", partition_cols=None)

    logger.info("Pipeline run completed successfully.")
    return stats


if __name__ == "__main__":
    logger.info("Executing flight data pipeline runner...")
    results = run_pipeline()
    results.show()