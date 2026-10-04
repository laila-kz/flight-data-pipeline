from unittest.mock import patch
from flight_pipeline.ingest_flights import OPENSKY_SCHEMA, ingest_flights
import requests


def test_opensky_schema_fields():
    field_names = OPENSKY_SCHEMA.fieldNames()
    expected_fields = [
        "icao24", "callsign", "origin_country", "time_position",
        "last_contact", "longitude", "latitude", "baro_altitude",
        "on_ground", "velocity"
    ]
    for field in expected_fields:
        assert field in field_names


@patch("flight_pipeline.ingest_flights.requests.get")
def test_ingest_flights_network_error(mock_get, spark):
    mock_get.side_effect = requests.exceptions.RequestException("API connection timeout")
    df = ingest_flights(spark=spark)

    assert df is not None
    assert df.count() == 0
    assert df.schema == OPENSKY_SCHEMA


@patch("flight_pipeline.ingest_flights.requests.get")
def test_ingest_flights_empty_payload(mock_get, spark):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"time": 1000, "states": None}

    df = ingest_flights(spark=spark)

    assert df is not None
    assert df.count() == 0
