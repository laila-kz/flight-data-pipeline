"""
Data Quality & Data Cleaning Module for Flight Data Pipeline.
Provides pure, composable PySpark functions to clean, cast, and validate flight datasets.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType, DoubleType, StringType


def cast_column_types(df: DataFrame) -> DataFrame:
    """Explicitly casts incoming DataFrame columns to their target Data Engineering types."""
    return (
        df.withColumn("icao24", F.trim(F.col("icao24").cast(StringType())))
        .withColumn("callsign", F.trim(F.col("callsign").cast(StringType())))
        .withColumn("origin_country", F.trim(F.col("origin_country").cast(StringType())))
        .withColumn("latitude", F.col("latitude").cast(DoubleType()))
        .withColumn("longitude", F.col("longitude").cast(DoubleType()))
        .withColumn("baro_altitude", F.col("baro_altitude").cast(DoubleType()))
        .withColumn("velocity", F.col("velocity").cast(DoubleType()))
        .withColumn("on_ground", F.col("on_ground").cast(BooleanType()))
    )


def filter_nulls(df: DataFrame, required_cols=None) -> DataFrame:
    """Removes rows containing nulls or empty strings in essential required columns."""
    if required_cols is None:
        required_cols = ["icao24", "origin_country"]

    df_clean = df
    for col_name in required_cols:
        df_clean = df_clean.filter(
            F.col(col_name).isNotNull() & (F.length(F.trim(F.col(col_name))) > 0)
        )
    return df_clean


def filter_coordinate_ranges(df: DataFrame) -> DataFrame:
    """Enforces geographic range checks on coordinates and altitude limits."""
    # Latitude must be between -90 and 90, Longitude between -180 and 180 (allowing nulls if unspecified)
    coord_cond = (
        (F.col("latitude").isNull() | ((F.col("latitude") >= -90.0) & (F.col("latitude") <= 90.0))) &
        (F.col("longitude").isNull() | ((F.col("longitude") >= -180.0) & (F.col("longitude") <= 180.0)))
    )

    # Altitude check: baro_altitude when present should be within valid physical limits (-1000m to 30000m)
    alt_cond = (
        F.col("baro_altitude").isNull() |
        ((F.col("baro_altitude") >= -1000.0) & (F.col("baro_altitude") <= 30000.0))
    )

    return df.filter(coord_cond & alt_cond)


def filter_velocity_range(df: DataFrame, max_velocity: float = 1000.0) -> DataFrame:
    """Filters out unrealistic velocity values (e.g. negative speeds or > max_velocity m/s)."""
    return df.filter(
        F.col("velocity").isNull() |
        ((F.col("velocity") >= 0.0) & (F.col("velocity") < max_velocity))
    )


def clean_flights(df: DataFrame) -> DataFrame:
    """
    Pure composite function that performs end-to-end data cleaning and validation on flight records.

    :param df: Input raw PySpark DataFrame
    :return: Cleaned and validated PySpark DataFrame
    """
    if df.rdd.isEmpty():
        return df

    typed_df = cast_column_types(df)
    null_filtered_df = filter_nulls(typed_df, ["icao24", "origin_country"])
    geo_filtered_df = filter_coordinate_ranges(null_filtered_df)
    clean_df = filter_velocity_range(geo_filtered_df)

    return clean_df
