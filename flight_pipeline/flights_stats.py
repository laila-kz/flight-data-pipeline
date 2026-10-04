"""
Aggregations and Analytics Transformations for Flight Data Pipeline.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def flight_stats(df: DataFrame) -> DataFrame:
    """Computes high-level KPI summary statistics across flight records."""
    return df.agg(
        F.count("*").alias("num_events"),
        F.countDistinct("icao24").alias("distinct_aircraft"),
        F.max("velocity").alias("max_velocity")
    )


def aircraft_by_country(df: DataFrame) -> DataFrame:
    """Aggregates distinct aircraft count grouped by origin country."""
    return (
        df.groupBy("origin_country")
        .agg(F.countDistinct("icao24").alias("num_aircraft"))
        .orderBy(F.col("num_aircraft").desc())
    )


def fastest_flights(df: DataFrame) -> DataFrame:
    """Extracts the top 10 fastest flight positions ordered by velocity descending."""
    return df.orderBy(F.col("velocity").desc()).limit(10)


def flights_on_ground(df: DataFrame) -> DataFrame:
    """Filters flight observations for aircraft currently reported on ground."""
    return df.filter(F.col("on_ground") == True)
