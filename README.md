# Live Flight Data Pipeline

A small, local flight data pipeline that ingests live aircraft state data from the OpenSky API, processes it with PySpark, computes summary statistics and precomputed views, and exposes an interactive Streamlit dashboard.

## Features
- Ingests realtime aircraft states from the OpenSky API
- Cleans and filters observations using Spark
- Computes aggregates and precomputed datasets (stats, aircraft by country, fastest flights, flights on ground)
- Writes outputs to `output/` as Parquet (preferred) or CSV (fallback)
- Streamlit dashboard for KPIs, charts and a world map of aircraft positions

## Requirements
- Python 3.8+ (or your environment's Python used by PySpark)
- PySpark
- requests
- pandas
- streamlit
- plotly

Install (example using pip):

```bash
pip install pyspark requests pandas streamlit plotly
```

If you use conda you may prefer:

```bash
conda create -n flight-pipeline python=3.9
conda activate flight-pipeline
pip install pyspark requests pandas streamlit plotly
```

## Project layout

- `flight_pipeline/`
  - `ingest_flights.py`  — pulls OpenSky API data and creates a Spark DataFrame
  - `clean_data.py`      — basic cleaning/filters for the DataFrame
  - `flights_stats.py`   — transforms and aggregated views
  - `run_pipeline.py`    — composes the pipeline and writes outputs to `output/`
  - `dashboard.py`       — Streamlit app that reads outputs and visualizes them
- `output/`              — pipeline outputs (CSV or Parquet)

## Running the pipeline

Run from the project root. This will ingest, clean, compute stats and write files to `output/`.

```bash
python flight_pipeline/run_pipeline.py
```

By default the runner writes CSV files. To enable Parquet output set the environment variable:

```bash
# Linux / macOS
export PIPELINE_ENABLE_PARQUET=1

# Windows PowerShell
$env:PIPELINE_ENABLE_PARQUET = '1'
```

Notes:
- The script creates a local SparkSession. Ensure your Python used by Spark is correct; `ingest_flights.py` sets `PYSPARK_PYTHON` to the running interpreter.
- `run_pipeline.py` contains an optional loop to re-run every 60s for a simple streaming behavior.

## Dashboard (Streamlit)

Start the dashboard after the pipeline has produced output files (CSV or Parquet) in `output/`.

```bash
streamlit run flight_pipeline/dashboard.py
```

The app reads precomputed datasets from `output/` and shows KPIs, a bar chart of aircraft by country, the top 10 fastest flights table, a flights-on-ground table, and a world map of aircraft positions.

## Output files

Typical files written to `output/`:
- `flights.csv` or `output/flights/` (Parquet)
- `stats.csv` or `output/stats/` (Parquet)
- `aircraft_by_country.csv` or `output/aircraft_by_country/`
- `fastest_flights.csv` or `output/fastest_flights/`
- `flights_on_ground.csv` or `output/flights_on_ground/`

## Development notes
- The pipeline is intentionally small and educational. You can extend cleaning logic, persist to a database, or replace the ad-hoc loop with a proper scheduler or streaming framework.
- If Spark filesystem writes fail on Windows, `run_pipeline.py` falls back to CSV writes.


