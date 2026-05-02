#what is a data_pipeline ?
#A data pipeline is a series of processes that extract, transform, and load (ETL) data from various sources to a destination, such as a data warehouse
#  or database. It involves collecting data from different sources, cleaning and transforming it into a usable format, and then loading it into a storage 
# system for analysis or further processing. Data pipelines are essential for managing and processing large volumes of data efficiently and ensuring that the 
# data is accurate and up-to-date for decision-making purposes.

#it mainly does three jobs :
#1. get data
#2. process data
#3. show results


#what is open sky : a web site that tracks real airplane flying in the sky 

#what is spark : super robot that processes huge data very fast.


#what we will do in this project :
# Open sky flights --> spark pipeline  --> flights statistics

#Ingest file : pulls flight data from openSky api and converts to dataframe :
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

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

spark = (
    SparkSession.builder.master("local[*]")
    .appName("FlightPipeline")
    .getOrCreate()
)


def _to_float(value):
    if value is None:
        return None
    return float(value)


def _to_int(value):
    if value is None:
        return None
    return int(value)


def _to_str(value):
    if value is None:
        return None
    return str(value).strip()


def _to_bool(value):
    if value is None:
        return None
    return bool(value)


def ingest_flights():
    url = "https://opensky-network.org/api/states/all"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    payload = response.json()
    states = payload.get("states") or []

    columns =[
        "icao24","callsign","origin_country","time_position",
        "last_contact","longitude","latitude","baro_altitude",
        "on_ground","velocity"
    ]

    schema = StructType(
        [
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
        ]
    )

    rows = []
    for s in states:
        # Normalize API types before creating the DataFrame to avoid Spark merge-type errors.
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

    df = spark.createDataFrame(rows, schema=schema)
    df = df.select(columns)
    return df

