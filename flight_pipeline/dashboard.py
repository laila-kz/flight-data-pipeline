"""
Live Flight Operations Dashboard.
Restrained, data-first internal analytics interface built with Streamlit & Plotly.
"""

from datetime import datetime
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from flight_pipeline.styles import inject_css
except ImportError:
    from styles import inject_css

# ==========================================
# 1. Page Config & Style Injection
# ==========================================
st.set_page_config(
    page_title="Live flight operations",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ==========================================
# 2. Data Loading & Lake Engine Detection
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_dataset(name: str) -> pd.DataFrame:
    """Loads dataset from parquet lake storage or fallback CSV."""
    parquet_dir = OUTPUT_DIR / name
    parquet_file = OUTPUT_DIR / f"{name}.parquet"
    csv_file = OUTPUT_DIR / f"{name}.csv"

    if parquet_dir.exists():
        try:
            return pd.read_parquet(parquet_dir)
        except Exception:
            pass
    if parquet_file.exists():
        try:
            return pd.read_parquet(parquet_file)
        except Exception:
            pass
    if csv_file.exists():
        try:
            return pd.read_csv(csv_file)
        except Exception:
            pass
    return pd.DataFrame()


flights_df = load_dataset("flights")

if flights_df.empty:
    st.error(
        f"No output data found in dataset path {OUTPUT_DIR}. "
        "Run 'python flight_pipeline/run_pipeline.py' first to generate pipeline outputs."
    )
    st.stop()

# Real storage sink detection
is_parquet = (OUTPUT_DIR / "flights").is_dir() or (OUTPUT_DIR / "flights.parquet").exists() or os.getenv("PIPELINE_ENABLE_PARQUET", "0") == "1"
sink_type = "Parquet" if is_parquet else "CSV"

# Field conversions
if "velocity" in flights_df.columns:
    flights_df["velocity"] = pd.to_numeric(flights_df["velocity"], errors="coerce").fillna(0.0)
    flights_df["velocity_kmh"] = (flights_df["velocity"] * 3.6).round(1)
else:
    flights_df["velocity"] = 0.0
    flights_df["velocity_kmh"] = 0.0

if "baro_altitude" in flights_df.columns:
    flights_df["baro_altitude"] = pd.to_numeric(flights_df["baro_altitude"], errors="coerce").fillna(0.0)
else:
    flights_df["baro_altitude"] = 0.0

if "on_ground" in flights_df.columns:
    flights_df["on_ground"] = flights_df["on_ground"].astype(bool)
else:
    flights_df["on_ground"] = False

if "latitude" in flights_df.columns:
    flights_df["latitude"] = pd.to_numeric(flights_df["latitude"], errors="coerce")
if "longitude" in flights_df.columns:
    flights_df["longitude"] = pd.to_numeric(flights_df["longitude"], errors="coerce")

# Calculate metrics without redundant math
total_flights = len(flights_df)
airborne_df = flights_df[~flights_df["on_ground"]]
ground_df = flights_df[flights_df["on_ground"]]

airborne_count = len(airborne_df)
ground_count = len(ground_df)
avg_velocity_kmh = airborne_df["velocity_kmh"].mean() if not airborne_df.empty else 0.0
max_velocity_kmh = flights_df["velocity_kmh"].max() if not flights_df.empty else 0.0

# Load auxiliary analytics datasets
country_df = load_dataset("aircraft_by_country")
if country_df.empty and not flights_df.empty:
    country_df = (
        flights_df.dropna(subset=["origin_country", "icao24"])
        .groupby("origin_country", as_index=False)["icao24"]
        .nunique()
        .rename(columns={"icao24": "num_aircraft"})
        .sort_values("num_aircraft", ascending=False)
    )

fastest_df = load_dataset("fastest_flights")
if fastest_df.empty and not flights_df.empty:
    fastest_df = flights_df.sort_values("velocity", ascending=False).head(10)

if "velocity" in fastest_df.columns:
    fastest_df["velocity_kmh"] = (pd.to_numeric(fastest_df["velocity"], errors="coerce") * 3.6).round(1)

# Timestamp calculation
now = datetime.utcnow()
last_sync_str = now.strftime("%H:%M:%S UTC")

# ==========================================
# 3. Sidebar Layout
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-heading">Pipeline</div>', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="sidebar-row">
            <span class="sidebar-label">Status</span>
            <span class="sidebar-val" style="display:flex; align-items:center; gap:6px;">
                <span class="status-dot ok"></span> Active
            </span>
        </div>
        <div class="sidebar-row" style="font-size:12px; color:var(--text-muted); margin-top:2px;">
            <span>OpenSky API → PySpark → Lakehouse</span>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    st.markdown('<hr style="border-color:var(--border); margin: 16px 0;">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-heading">Refresh</div>', unsafe_allow_html=True)
    refresh_interval = st.number_input(
        "Refresh interval (s)", min_value=10, max_value=600, value=60, step=10, label_visibility="collapsed"
    )
    if st.button("Refresh now", use_container_width=True):
        st.rerun()

    st.markdown('<hr style="border-color:var(--border); margin: 16px 0;">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-heading">Telemetry</div>', unsafe_allow_html=True)
    st.markdown(
        f'''
        <div class="sidebar-row">
            <span class="sidebar-label">Records</span>
            <span class="sidebar-val">{total_flights:,}</span>
        </div>
        <div class="sidebar-row">
            <span class="sidebar-label">Storage sink</span>
            <span class="sidebar-val">{sink_type}</span>
        </div>
        ''',
        unsafe_allow_html=True,
    )

# ==========================================
# 4. Header & Restrained KPI Row
# ==========================================
st.markdown(
    f'''
    <div class="app-header">
        <h1 class="app-title">Live flight operations</h1>
        <div class="app-subtitle">
            OpenSky state vectors · PySpark · {sink_type}
            <span>·</span>
            <span class="status-dot ok"></span> Updated {last_sync_str}
        </div>
    </div>
    ''',
    unsafe_allow_html=True,
)

# 4 Equal-height, single-line KPI Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(
        f'''
        <div class="kpi-card" title="Active in-flight state vectors">
            <div class="kpi-label">Airborne</div>
            <div class="kpi-value">{airborne_count:,}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f'''
        <div class="kpi-card" title="Aircraft taxied or stationary on ground">
            <div class="kpi-label">On ground</div>
            <div class="kpi-value">{ground_count:,}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

with kpi3:
    st.markdown(
        f'''
        <div class="kpi-card" title="Average speed of airborne aircraft">
            <div class="kpi-label">Avg speed</div>
            <div class="kpi-value">{avg_velocity_kmh:.0f} <span class="kpi-unit">km/h</span></div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

with kpi4:
    st.markdown(
        f'''
        <div class="kpi-card" title="Maximum speed recorded across fleet">
            <div class="kpi-label">Peak speed</div>
            <div class="kpi-value">{max_velocity_kmh:.0f} <span class="kpi-unit">km/h</span></div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ==========================================
# 5. Flat Underline Tabs & Components
# ==========================================
tab_map, tab_analytics, tab_fleet = st.tabs(["Live map", "Analytics", "Fleet data"])

# ------------------------------------------
# TAB 1: Plotly Map with Low Opacity Markers
# ------------------------------------------
with tab_map:
    map_df = flights_df.dropna(subset=["latitude", "longitude"]).copy()

    if map_df.empty:
        st.info("No geographic coordinate data available.")
    else:
        fig_map = px.scatter_geo(
            map_df,
            lat="latitude",
            lon="longitude",
            hover_name="callsign",
            hover_data={
                "icao24": True,
                "origin_country": True,
                "velocity_kmh": ":.0f",
                "baro_altitude": ":,.0f",
                "on_ground": True,
                "latitude": False,
                "longitude": False,
            },
            color="velocity_kmh",
            color_continuous_scale="cividis",
            projection="natural earth",
            height=560,
        )

        fig_map.update_traces(marker=dict(size=4, opacity=0.55))

        fig_map.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#E6EAF0", size=12),
            margin=dict(l=0, r=0, t=10, b=0),
            geo=dict(
                bgcolor="#0E1116",
                showland=True,
                landcolor="#151A21",
                showocean=True,
                oceancolor="#0E1116",
                showlakes=True,
                lakecolor="#0E1116",
                showcountries=True,
                countrycolor="#242C37",
                coastlinecolor="#242C37",
            ),
            coloraxis_colorbar=dict(
                title=dict(text="Speed (km/h)", font=dict(color="#8A94A3", size=11)),
                thickness=10,
                len=0.6,
                tickfont=dict(color="#8A94A3", size=11),
            ),
        )

        st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})

# ------------------------------------------
# TAB 2: Clean Analytics Charts
# ------------------------------------------
with tab_analytics:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="sidebar-heading" style="margin-top:0;">Aircraft by country</div>', unsafe_allow_html=True)
        if not country_df.empty:
            top_countries = country_df.sort_values("num_aircraft", ascending=True).tail(10)
            fig_country = px.bar(
                top_countries,
                x="num_aircraft",
                y="origin_country",
                orientation="h",
                color_discrete_sequence=["#4C9AFF"],
                height=380,
            )

            fig_country.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#8A94A3", size=11),
                xaxis=dict(showgrid=False, title="Aircraft count", color="#8A94A3"),
                yaxis=dict(showgrid=False, title="", color="#8A94A3"),
                margin=dict(l=0, r=0, t=10, b=0),
            )

            st.plotly_chart(fig_country, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No country analytics data available.")

    with col2:
        st.markdown('<div class="sidebar-heading" style="margin-top:0;">Speed distribution</div>', unsafe_allow_html=True)
        if not flights_df.empty:
            fig_hist = px.histogram(
                flights_df[flights_df["velocity_kmh"] > 0],
                x="velocity_kmh",
                nbins=25,
                color_discrete_sequence=["#4C9AFF"],
                height=380,
            )

            fig_hist.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#8A94A3", size=11),
                xaxis=dict(showgrid=False, title="Speed (km/h)", color="#8A94A3"),
                yaxis=dict(showgrid=False, title="Count", color="#8A94A3"),
                margin=dict(l=0, r=0, t=10, b=0),
                bargap=0.1,
            )

            st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

# ------------------------------------------
# TAB 3: Fleet Data Tables
# ------------------------------------------
with tab_fleet:
    tcol1, tcol2 = st.columns(2, gap="large")

    with tcol1:
        st.markdown('<div class="sidebar-heading" style="margin-top:0;">Top 10 fastest flights</div>', unsafe_allow_html=True)
        if not fastest_df.empty:
            display_fastest = fastest_df[
                [c for c in ["callsign", "icao24", "origin_country", "velocity_kmh", "baro_altitude"] if c in fastest_df.columns]
            ].copy()

            st.dataframe(
                display_fastest,
                column_config={
                    "callsign": st.column_config.TextColumn("Callsign"),
                    "icao24": st.column_config.TextColumn("ICAO24"),
                    "origin_country": st.column_config.TextColumn("Origin country"),
                    "velocity_kmh": st.column_config.NumberColumn("Speed (km/h)", format="%.0f km/h"),
                    "baro_altitude": st.column_config.NumberColumn("Altitude (m)", format="%'.0f m"),
                },
                use_container_width=True,
                hide_index=True,
                height=360,
            )

    with tcol2:
        st.markdown('<div class="sidebar-heading" style="margin-top:0;">Grounded aircraft</div>', unsafe_allow_html=True)
        if not ground_df.empty:
            display_ground = ground_df[
                [c for c in ["callsign", "icao24", "origin_country", "latitude", "longitude"] if c in ground_df.columns]
            ].head(10).copy()

            st.dataframe(
                display_ground,
                column_config={
                    "callsign": st.column_config.TextColumn("Callsign"),
                    "icao24": st.column_config.TextColumn("ICAO24"),
                    "origin_country": st.column_config.TextColumn("Origin country"),
                    "latitude": st.column_config.NumberColumn("Latitude", format="%.4f"),
                    "longitude": st.column_config.NumberColumn("Longitude", format="%.4f"),
                },
                use_container_width=True,
                hide_index=True,
                height=360,
            )
        else:
            st.info("No grounded aircraft reported.")