# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title=" Live Flight Dashboard", layout="wide")

st.markdown(
    """
    <style>
        @import url('https://fonts.google.com/specimen/Lato');

        html, body, [class*="css"] {
            font-family: 'Manrope', sans-serif;
        }

        .dashboard-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #0f2742;
            margin-bottom: 0.1rem;
            line-height: 1.1;
        }

        .dashboard-subtitle {
            color: #3f5368;
            font-size: 1rem;
            font-weight: 500;
            margin-bottom: 1.2rem;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #17324d;
            margin-top: 0.4rem;
            margin-bottom: 0.6rem;
        }

        .kpi-card {
            background: linear-gradient(135deg, #f5f9ff 0%, #e7f0ff 100%);
            border: 1px solid #d1e0f5;
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow: 0 3px 10px rgba(29, 53, 87, 0.08);
        }

        .kpi-label {
            color: #37526d;
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }

        .kpi-value {
            color: #0f2742;
            font-size: 1.6rem;
            font-weight: 800;
            line-height: 1.1;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Resolve output folder from project root so dashboard works from any current directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

logo_candidates = [
    Path(__file__).resolve().parent / "Logo.png",
    PROJECT_ROOT / "Logo2.png",
    PROJECT_ROOT / "assets" / "Logo2.png",
]
logo_path = next((path for path in logo_candidates if path.exists()), None)

title_logo_col, title_text_col = st.columns([1, 10], gap="small")
with title_logo_col:
    if logo_path:
        st.image(str(logo_path), width=76)
    else:
        st.markdown(
            "<div style='font-size:2.1rem; line-height:1.8; text-align:center;'>✈</div>",
            unsafe_allow_html=True,
        )

with title_text_col:
    st.markdown('<div class="dashboard-title">Live Flight Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dashboard-subtitle">Realtime aircraft data from the OpenSky API processed with Spark</div>',
        unsafe_allow_html=True,
    )


def load_dataset(name: str):
    parquet_dir = OUTPUT_DIR / name
    parquet_file = OUTPUT_DIR / f"{name}.parquet"
    csv_file = OUTPUT_DIR / f"{name}.csv"

    if parquet_dir.exists():
        return pd.read_parquet(parquet_dir)
    if parquet_file.exists():
        return pd.read_parquet(parquet_file)
    if csv_file.exists():
        return pd.read_csv(csv_file)
    return None


flights_df = load_dataset("flights")
if flights_df is None:
    st.error(
        f"No output data found in {OUTPUT_DIR}. Run the pipeline first to generate flights data."
    )
    st.stop()

stats_df = load_dataset("stats")
if stats_df is None or stats_df.empty:
    stats_df = pd.DataFrame(
        [
            {
                "num_events": len(flights_df),
                "distinct_aircraft": flights_df["icao24"].nunique(dropna=True),
                "max_velocity": pd.to_numeric(
                    flights_df.get("velocity", pd.Series(dtype="float")),
                    errors="coerce",
                ).max(),
            }
        ]
    )

aircraft_country_df = load_dataset("aircraft_by_country")
if aircraft_country_df is None or aircraft_country_df.empty:
    aircraft_country_df = (
        flights_df.dropna(subset=["origin_country", "icao24"])
        .groupby("origin_country", as_index=False)["icao24"]
        .nunique()
        .rename(columns={"icao24": "num_aircraft"})
        .sort_values("num_aircraft", ascending=False)
    )

fastest_df = load_dataset("fastest_flights")
if fastest_df is None or fastest_df.empty:
    fastest_df = flights_df.sort_values("velocity", ascending=False).head(10)

ground_df = load_dataset("flights_on_ground")
if ground_df is None:
    ground_df = flights_df[flights_df.get("on_ground", False) == True]

if "velocity" in flights_df.columns:
    flights_df["velocity"] = pd.to_numeric(flights_df["velocity"], errors="coerce")
if "velocity" in fastest_df.columns:
    fastest_df["velocity"] = pd.to_numeric(fastest_df["velocity"], errors="coerce")


def format_kpi_value(value, decimals=0):
    if pd.isna(value):
        return "N/A"
    if decimals == 0:
        return f"{int(value):,}"
    return f"{float(value):,.{decimals}f}"

# ==============================
# 1️⃣ Top KPIs
# ==============================
st.markdown('<div class="section-title">📊 Key Performance Indicators</div>', unsafe_allow_html=True)

kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

with kpi_col1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">🧾 Total Events</div>
            <div class="kpi-value">{format_kpi_value(stats_df['num_events'].values[0])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">🛩 Distinct Aircraft</div>
            <div class="kpi-value">{format_kpi_value(stats_df['distinct_aircraft'].values[0])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi_col3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">⚡ Max Velocity (m/s)</div>
            <div class="kpi-value">{format_kpi_value(stats_df['max_velocity'].values[0], 2)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#fbfdff",
        plot_bgcolor="#fbfdff",
        font=dict(family="Manrope, sans-serif", color="#16324a"),
        margin=dict(l=30, r=20, t=60, b=30),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#d7e3f3", zeroline=False, title_standoff=8)
    fig.update_yaxes(showgrid=True, gridcolor="#d7e3f3", zeroline=False, title_standoff=8)
    return fig


left_col, right_col = st.columns([1, 1], gap="large")

# ==============================
# 2️⃣ Aircraft by Country Bar Chart
# ==============================
with left_col:
    with st.container(border=True):
        st.markdown('<div class="section-title">🌍 Aircraft by Country</div>', unsafe_allow_html=True)
        chart_df = aircraft_country_df.sort_values("num_aircraft", ascending=False).head(15)
        fig_country = px.bar(
            chart_df,
            x="origin_country",
            y="num_aircraft",
            title="Number of Aircraft per Country",
            labels={"origin_country": "Country", "num_aircraft": "Aircraft Count"},
            color="num_aircraft",
            color_continuous_scale="Blues",
            height=430,
        )
        fig_country = style_figure(fig_country)
        st.plotly_chart(fig_country, use_container_width=True)

# ==============================
# 3️⃣ Top 10 Fastest Flights
# ==============================
with right_col:
    with st.container(border=True):
        st.markdown('<div class="section-title">⚡ Top 10 Fastest Flights</div>', unsafe_allow_html=True)
        fastest_display = fastest_df[[c for c in ["icao24", "callsign", "origin_country", "velocity"] if c in fastest_df.columns]].copy()
        if "velocity" in fastest_display.columns:
            fastest_display["velocity"] = fastest_display["velocity"].round(2)
        st.dataframe(
            fastest_display,
            use_container_width=True,
            hide_index=True,
            height=430,
        )

# ==============================
# 4️⃣ Flights on the Ground
# ==============================
with st.container(border=True):
    st.markdown('<div class="section-title">🛬 Flights on the Ground</div>', unsafe_allow_html=True)
    ground_display = ground_df[[c for c in ["icao24", "callsign", "origin_country", "longitude", "latitude"] if c in ground_df.columns]].copy()
    st.dataframe(ground_display, use_container_width=True, hide_index=True, height=260)

# ==============================
# 5️⃣ Aircraft Map
# ==============================
with st.container(border=True):
    st.markdown('<div class="section-title">✈️ Aircraft Positions on World Map</div>', unsafe_allow_html=True)

    flights_map_df = flights_df.dropna(subset=["latitude", "longitude"]).copy()
    if "velocity" in flights_map_df.columns:
        flights_map_df["velocity"] = pd.to_numeric(flights_map_df["velocity"], errors="coerce")
    else:
        flights_map_df["velocity"] = 0

    fig_map = px.scatter_geo(
        flights_map_df,
        lat="latitude",
        lon="longitude",
        hover_name="icao24",
        hover_data={"velocity": ":.2f", "origin_country": True, "on_ground": True},
        color="velocity",
        color_continuous_scale="Turbo",
        opacity=0.75,
        title="Live Aircraft Positions",
        projection="natural earth",
        height=520,
    )
    fig_map.update_traces(marker=dict(size=6, line=dict(width=0.5, color="#f8fbff")))
    fig_map.update_layout(
        template="plotly_white",
        paper_bgcolor="#fbfdff",
        font=dict(family="Manrope, sans-serif", color="#16324a"),
        margin=dict(l=10, r=10, t=60, b=10),
        geo=dict(showland=True, landcolor="#edf3fb", showocean=True, oceancolor="#dceafb"),
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ==============================
# Optional: Auto-refresh
# ==============================
st.sidebar.header("Dashboard Controls")
refresh_interval = st.sidebar.number_input(
    "Refresh interval (seconds)", min_value=10, max_value=600, value=60, step=10
)

st.sidebar.markdown(
    f"Dashboard will refresh every **{refresh_interval} seconds**. "
    "Run the pipeline script periodically to update the output files (parquet or csv)."
)