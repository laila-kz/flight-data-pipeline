import pytest
from flight_pipeline.clean_data import (
    cast_column_types,
    clean_flights,
    filter_coordinate_ranges,
    filter_nulls,
    filter_velocity_range,
)
from flight_pipeline.ingest_flights import OPENSKY_SCHEMA


def test_cast_column_types(spark):
    data = [
        (" icao1 ", " call1 ", " United States ", "12.34", "-56.78", "1000.0", "true", "250.5")
    ]
    columns = ["icao24", "callsign", "origin_country", "latitude", "longitude", "baro_altitude", "on_ground", "velocity"]
    df = spark.createDataFrame(data, columns)
    typed_df = cast_column_types(df)
    row = typed_df.collect()[0]

    assert row["icao24"] == "icao1"
    assert row["origin_country"] == "United States"
    assert row["latitude"] == 12.34
    assert row["longitude"] == -56.78
    assert row["baro_altitude"] == 1000.0
    assert row["on_ground"] is True
    assert row["velocity"] == 250.5


def test_filter_nulls(spark):
    data = [
        ("icao1", "United States"),
        (None, "United States"),
        ("icao2", None),
        ("   ", "Canada"),
    ]
    df = spark.createDataFrame(data, ["icao24", "origin_country"])
    filtered_df = filter_nulls(df, ["icao24", "origin_country"])
    assert filtered_df.count() == 1
    assert filtered_df.collect()[0]["icao24"] == "icao1"


def test_filter_coordinate_ranges(spark):
    data = [
        ("icao1", 45.0, -90.0, 5000.0),      # Valid
        ("icao2", 100.0, -90.0, 5000.0),     # Invalid Lat (>90)
        ("icao3", 45.0, -200.0, 5000.0),    # Invalid Lon (<-180)
        ("icao4", 45.0, -90.0, 40000.0),     # Invalid Altitude (>30000)
    ]
    columns = ["icao24", "latitude", "longitude", "baro_altitude"]
    df = spark.createDataFrame(data, columns)
    filtered_df = filter_coordinate_ranges(df)

    assert filtered_df.count() == 1
    assert filtered_df.collect()[0]["icao24"] == "icao1"


def test_filter_velocity_range(spark):
    data = [
        ("icao1", 250.0),   # Valid
        ("icao2", -10.0),   # Invalid negative
        ("icao3", 1500.0),  # Invalid > 1000
    ]
    df = spark.createDataFrame(data, ["icao24", "velocity"])
    filtered_df = filter_velocity_range(df, max_velocity=1000.0)

    assert filtered_df.count() == 1
    assert filtered_df.collect()[0]["icao24"] == "icao1"


def test_clean_flights(spark):
    rows = [
        ("a1", "AAL1", "USA", 100, 100, -80.0, 25.0, 1000.0, False, 200.0),   # Valid
        (None, "AAL2", "USA", 100, 100, -80.0, 25.0, 1000.0, False, 200.0),   # Null icao24
        ("a3", "AAL3", "USA", 100, 100, -80.0, 25.0, 1000.0, False, 1500.0),  # Invalid speed
    ]
    df = spark.createDataFrame(rows, schema=OPENSKY_SCHEMA)
    cleaned_df = clean_flights(df)

    assert cleaned_df.count() == 1
    assert cleaned_df.collect()[0]["icao24"] == "a1"
