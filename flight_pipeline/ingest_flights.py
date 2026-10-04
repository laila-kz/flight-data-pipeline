import logging
import os
import sys

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)
import requests

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Explicit PySpark Schema for OpenSky API State Vectors
OPENSKY_SCHEMA = StructType([
    StructField("icao24", StringType(), True),
    StructField("callsign", StringType(), True),
    StructField("origin_country", StringType(), True),
    StructField("time_position", LongType(), True),
    StructField("last_contact", LongType(), True),
    StructField("longitude", DoubleType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("baro_altitude", DoubleType(), True),
    StructField("on_ground", BooleanType(), True),
    StructField("velocity", DoubleType(), True),
])


def get_spark_session() -> SparkSession:
    """Get or create the local PySpark Session."""
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    return (
        SparkSession.builder.master("local[*]")
        .appName("FlightPipeline")
        .getOrCreate()
    )


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _to_str(value):
    if value is None:
        return None
    val_str = str(value).strip()
    return val_str if val_str else None


def _to_bool(value):
    if value is None:
        return None
    return bool(value)


def ingest_flights(spark: SparkSession = None, url: str = "https://opensky-network.org/api/states/all", timeout: int = 20):
    """
    Ingests live flight state vectors from OpenSky API into a PySpark DataFrame.
    Applies explicit schema definition and robust network/status error handling.
    """
    if spark is None:
        spark = get_spark_session()

    try:
        logger.info("Fetching flight states from OpenSky API: %s", url)
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        logger.error("HTTP request failure when contacting OpenSky API: %s", exc)
        return spark.createDataFrame([], schema=OPENSKY_SCHEMA)
    except Exception as exc:
        logger.error("Unexpected error during API response parsing: %s", exc)
        return spark.createDataFrame([], schema=OPENSKY_SCHEMA)

    states = payload.get("states") if isinstance(payload, dict) else None
    if not states:
        logger.warning("OpenSky API returned empty state payload.")
        return spark.createDataFrame([], schema=OPENSKY_SCHEMA)

    logger.info("Received %d raw flight records from API response.", len(states))

    columns = [
        "icao24", "callsign", "origin_country", "time_position",
        "last_contact", "longitude", "latitude", "baro_altitude",
        "on_ground", "velocity"
    ]

    rows = []
    for s in states:
        if not isinstance(s, list) or len(s) == 0:
            continue
        rows.append(
            [
                _to_str(s[0]) if len(s) > 0 else None,
                _to_str(s[1]) if len(s) > 1 else None,
                _to_str(s[2]) if len(s) > 2 else None,
                _to_int(s[3]) if len(s) > 3 else None,
                _to_int(s[4]) if len(s) > 4 else None,
                _to_float(s[5]) if len(s) > 5 else None,
                _to_float(s[6]) if len(s) > 6 else None,
                _to_float(s[7]) if len(s) > 7 else None,
                _to_bool(s[8]) if len(s) > 8 else None,
                _to_float(s[9]) if len(s) > 9 else None,
            ]
        )

    df = spark.createDataFrame(rows, schema=OPENSKY_SCHEMA)
    return df.select(columns)
