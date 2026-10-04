import pytest
from flight_pipeline.flights_stats import (
    aircraft_by_country,
    fastest_flights,
    flight_stats,
    flights_on_ground,
)
from flight_pipeline.ingest_flights import OPENSKY_SCHEMA


@pytest.fixture
def sample_flights_df(spark):
    rows = [
        ("a1", "CALL1", "USA", 100, 100, -80.0, 25.0, 1000.0, False, 200.0),
        ("a2", "CALL2", "USA", 100, 100, -80.0, 25.0, 1000.0, True, 300.0),
        ("a3", "CALL3", "Canada", 100, 100, -80.0, 25.0, 1000.0, False, 150.0),
    ]
    return spark.createDataFrame(rows, schema=OPENSKY_SCHEMA)


def test_flight_stats(sample_flights_df):
    stats_df = flight_stats(sample_flights_df)
    row = stats_df.collect()[0]

    assert row["num_events"] == 3
    assert row["distinct_aircraft"] == 3
    assert row["max_velocity"] == 300.0


def test_aircraft_by_country(sample_flights_df):
    country_df = aircraft_by_country(sample_flights_df)
    rows = country_df.collect()

    assert len(rows) == 2
    assert rows[0]["origin_country"] == "USA"
    assert rows[0]["num_aircraft"] == 2
    assert rows[1]["origin_country"] == "Canada"
    assert rows[1]["num_aircraft"] == 1


def test_fastest_flights(sample_flights_df):
    fastest_df = fastest_flights(sample_flights_df)
    rows = fastest_df.collect()

    assert rows[0]["icao24"] == "a2"
    assert rows[0]["velocity"] == 300.0


def test_flights_on_ground(sample_flights_df):
    ground_df = flights_on_ground(sample_flights_df)
    rows = ground_df.collect()

    assert len(rows) == 1
    assert rows[0]["icao24"] == "a2"
    assert rows[0]["on_ground"] is True
