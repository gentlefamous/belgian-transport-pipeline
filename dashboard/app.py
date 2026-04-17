"""Belgian Public Transport Intelligence Dashboard.

Displays real-time delay analytics from the Belgian transport pipeline.
Run with: streamlit run dashboard/app.py
"""

import duckdb
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page config
st.set_page_config(
    page_title="Belgian Rail Delay Intelligence Platform",
    page_icon="🚂",
    layout="wide",
)

# Database connection
DB_PATH = "dbt_models/belgian_transport/warehouse.duckdb"


@st.cache_data(ttl=300)
def load_delay_summary():
    """Load pre-computed delay summary from dbt mart."""
    conn = duckdb.connect(DB_PATH, read_only=True)
    df = conn.sql("SELECT * FROM main.mart_delay_summary").fetchdf()
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_departures():
    """Load departure-level data from fact table."""
    conn = duckdb.connect(DB_PATH, read_only=True)
    df = conn.sql(
        """
        SELECT f.*, s.station_name_primary
        FROM main.fct_delays f
        LEFT JOIN main.dim_stations s ON f.station_id = s.station_id
    """
    ).fetchdf()
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_station_list():
    """Load list of stations."""
    conn = duckdb.connect(DB_PATH, read_only=True)
    df = conn.sql(
        "SELECT station_id, station_name, station_name_primary FROM main.dim_stations ORDER BY station_name_primary"
    ).fetchdf()
    conn.close()
    return df


# Load data
try:
    summary = load_delay_summary()
    departures = load_departures()
    stations = load_station_list()
except Exception as e:
    st.error(f"Could not connect to database. Run the pipeline first.\n\nError: {e}")
    st.stop()

# ===== HEADER =====
st.title("🚂 Belgian Rail Delay Intelligence Platform")
st.markdown("Real-time delay analytics for SNCB/NMBS train departures across Belgium")

# Show analysis period
min_date = departures["departure_date"].min()
max_date = departures["departure_date"].max()
unique_dates = departures["departure_date"].nunique()
st.caption(f"📅 Analysis period: **{min_date}** to **{max_date}** ({unique_dates} days of data)")
st.markdown("---")

# ===== KPI CARDS =====
col1, col2, col3, col4 = st.columns(4)

total_departures = int(summary["total_departures"].sum())
total_delayed = int(summary["delayed_departures"].sum())
overall_delay_rate = round(total_delayed / total_departures * 100, 1) if total_departures > 0 else 0
avg_delay = (
    round(departures[departures["is_delayed"]]["delay_minutes"].mean(), 1)
    if len(departures[departures["is_delayed"]]) > 0
    else 0
)

col1.metric("Total Departures", f"{total_departures:,}")
col2.metric("Delayed Trains", f"{total_delayed:,}")
col3.metric("Delay Rate", f"{overall_delay_rate}%")
col4.metric("Avg Delay (when late)", f"{avg_delay} min")

st.markdown("---")

# ===== DELAY BY STATION =====
st.subheader("📊 Delay Rate by Station")

station_summary = (
    summary.groupby("station_name_primary")
    .agg(
        total=("total_departures", "sum"),
        delayed=("delayed_departures", "sum"),
        avg_delay=("avg_delay_minutes", "mean"),
    )
    .reset_index()
)
station_summary["delay_rate"] = round(station_summary["delayed"] / station_summary["total"] * 100, 1)
station_summary = station_summary.sort_values("delay_rate", ascending=True)

fig_stations = px.bar(
    station_summary,
    x="delay_rate",
    y="station_name_primary",
    orientation="h",
    color="delay_rate",
    color_continuous_scale="RdYlGn_r",
    labels={"delay_rate": "Delay Rate (%)", "station_name_primary": "Station"},
    title="Which stations have the most delays?",
)
fig_stations.update_layout(height=300, showlegend=False)
st.plotly_chart(fig_stations, use_container_width=True)

# ===== DELAY BY TIME OF DAY =====
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🕐 Delays by Hour of Day")

    hourly = (
        summary.groupby("departure_hour")
        .agg(
            total=("total_departures", "sum"),
            delayed=("delayed_departures", "sum"),
        )
        .reset_index()
    )
    hourly["delay_rate"] = round(hourly["delayed"] / hourly["total"] * 100, 1)

    fig_hourly = px.line(
        hourly,
        x="departure_hour",
        y="delay_rate",
        markers=True,
        labels={"departure_hour": "Hour of Day", "delay_rate": "Delay Rate (%)"},
        title="When are delays most likely?",
    )
    fig_hourly.update_layout(height=300)
    st.plotly_chart(fig_hourly, use_container_width=True)

with col_right:
    st.subheader("🌅 Delays by Time Period")

    period_order = ["Morning", "Afternoon", "Evening", "Night"]
    period = (
        summary.groupby("time_period")
        .agg(
            total=("total_departures", "sum"),
            delayed=("delayed_departures", "sum"),
            avg_delay=("avg_delay_minutes", "mean"),
        )
        .reset_index()
    )
    period["delay_rate"] = round(period["delayed"] / period["total"] * 100, 1)
    period["time_period"] = period["time_period"].astype("category")
    period["time_period"] = period["time_period"].cat.set_categories(period_order)
    period = period.sort_values("time_period")

    fig_period = px.bar(
        period,
        x="time_period",
        y="delay_rate",
        color="avg_delay",
        color_continuous_scale="OrRd",
        labels={"time_period": "Time Period", "delay_rate": "Delay Rate (%)", "avg_delay": "Avg Delay (min)"},
        title="Which part of the day is worst?",
    )
    fig_period.update_layout(height=300)
    st.plotly_chart(fig_period, use_container_width=True)

# ===== DELAY HEATMAP =====
st.subheader("🗺️ Delay Heatmap: Station × Hour")

heatmap_data = summary.pivot_table(
    values="delay_rate_pct",
    index="station_name_primary",
    columns="departure_hour",
    aggfunc="mean",
    fill_value=0,
)

fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=heatmap_data.values,
        x=[f"{h}:00" for h in heatmap_data.columns],
        y=heatmap_data.index,
        colorscale="RdYlGn_r",
        text=heatmap_data.values.round(1),
        texttemplate="%{text}%",
        textfont={"size": 10},
        colorbar=dict(title="Delay %"),
    )
)
fig_heatmap.update_layout(
    title="Delay Rate (%) by Station and Hour",
    height=300,
    xaxis_title="Hour of Day",
    yaxis_title="Station",
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# ===== OCCUPANCY ANALYSIS =====
st.subheader("👥 Delay Rate by Occupancy Level")

occ = (
    departures.groupby("occupancy")
    .agg(
        total=("departure_key", "count"),
        delayed=("is_delayed", "sum"),
        avg_delay=("delay_minutes", "mean"),
    )
    .reset_index()
)
occ["delay_rate"] = round(occ["delayed"] / occ["total"] * 100, 1)
occ_order = ["low", "medium", "high", "unknown"]
occ["occupancy"] = occ["occupancy"].astype("category")
occ["occupancy"] = occ["occupancy"].cat.set_categories(occ_order)
occ = occ.sort_values("occupancy")

fig_occ = px.bar(
    occ,
    x="occupancy",
    y="delay_rate",
    color="total",
    labels={"occupancy": "Occupancy Level", "delay_rate": "Delay Rate (%)", "total": "Total Trains"},
    title="Are crowded trains more likely to be delayed?",
)
fig_occ.update_layout(height=300)
st.plotly_chart(fig_occ, use_container_width=True)

# ===== FOOTER =====
st.markdown("---")
st.markdown(
    """
**Data Source:** [iRail API](https://api.irail.be) — Real-time SNCB/NMBS Belgian railway data

**Pipeline:** Kafka → PySpark → dbt → DuckDB | **Infrastructure:** Terraform on Azure | **CI/CD:** GitHub Actions

**GitHub:** [belgian-transport-pipeline](https://github.com/gentlefamous/belgian-transport-pipeline)
"""
)
