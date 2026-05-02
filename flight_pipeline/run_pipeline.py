# the pipleline runner 

import os
import time

from clean_data import clean_flights
from ingest_flights import ingest_flights
from flights_stats import (
    aircraft_by_country,
    fastest_flights,
    flight_stats,
    flights_on_ground,
)


ENABLE_PARQUET = os.getenv("PIPELINE_ENABLE_PARQUET", "0") == "1"


def _save_csv(df, csv_path):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.toPandas().to_csv(csv_path, index=False)
    print(f"Saved CSV: {csv_path}")


def _save_with_fallback(df, parquet_path, csv_path):
    if not ENABLE_PARQUET:
        _save_csv(df, csv_path)
        return

    try:
        df.write.mode("overwrite").parquet(parquet_path)
        print(f"Saved parquet: {parquet_path}")
    except Exception as exc:
        # Some Windows Java/Hadoop setups fail on Spark filesystem writes.
        print(f"Parquet write failed for {parquet_path}: {exc}")
        print(f"Falling back to CSV: {csv_path}")
        _save_csv(df, csv_path)

def run_pipeline():
    df = ingest_flights()
    df_clean = clean_flights(df)
    stats = flight_stats(df_clean)
    country = aircraft_by_country(df_clean)
    fastest = fastest_flights(df_clean)
    on_ground = flights_on_ground(df_clean)

    # save aircraft positions
    _save_with_fallback(df_clean, "output/flights", "output/flights.csv")

    # save stats
    _save_with_fallback(stats, "output/stats", "output/stats.csv")

    # save precomputed dashboard datasets
    _save_with_fallback(
        country,
        "output/aircraft_by_country",
        "output/aircraft_by_country.csv",
    )
    _save_with_fallback(
        fastest,
        "output/fastest_flights",
        "output/fastest_flights.csv",
    )
    _save_with_fallback(
        on_ground,
        "output/flights_on_ground",
        "output/flights_on_ground.csv",
    )

    return stats
if __name__ == "__main__":
    print("Running flight pipeline...")
    results = run_pipeline()
    print("Pipeline results:")
    results.show()

    # Addition : make it run like a streaming pipline by adding a loop and sleep time
    while True:
        stats = run_pipeline()
        print("Pipeline results:")
        stats.show()
        time.sleep(60)  # sleep for 60 seconds before running the pipeline again