import os
import sys
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    """Provides a local PySpark SparkSession for test execution."""
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    session = (
        SparkSession.builder.master("local[1]")
        .appName("FlightPipelineTestSession")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    yield session
    session.stop()
