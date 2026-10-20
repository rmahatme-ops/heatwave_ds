
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Heatwave Watch",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ Heatwave Watch")
st.caption(
    "Climate Intelligence for Heatwave Monitoring "
    "and Early Warning"
)

# Dataset used: heatwave_data.csv
df = pd.read_csv("heatwave_data.csv")

# Clean the supplied CSV
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["tmax"] = pd.to_numeric(df["tmax"], errors="coerce")
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

df = df.dropna(
    subset=["region", "date", "lat", "lon", "tmax"]
)

regions = sorted(df["region"].unique())

st.sidebar.header("Search observations")

region = st.sidebar.selectbox(
    "Select region", regions
)

start = st.sidebar.date_input(
    "Start date", df["date"].min().date()
)

end = st.sidebar.date_input(
    "End date", df["date"].max().date()
)

threshold = st.sidebar.slider(
    "Hot-day threshold (°C)",
    30.0, 50.0, 40.0, 0.5
)

if start > end:
    st.error("Start date must be before end date.")
    st.stop()

# Dataset used: cleaned CSV for the selected region
result = df[
    (df["region"] == region) &
    (df["date"].dt.date >= start) &
    (df["date"].dt.date <= end)
].copy()

if result.empty:
    st.warning("No observations found.")
    st.stop()

a, b, c, d = st.columns(4)

a.metric("Records", f"{len(result):,}")
b.metric("Average Tmax", f"{result['tmax'].mean():.2f} °C")
c.metric("Highest Tmax", f"{result['tmax'].max():.2f} °C")
d.metric(
    "Records above threshold",
    int((result["tmax"] >= threshold).sum())
)

# Chart 1: Daily average maximum temperature
daily = result.groupby(
    "date", as_index=False
)["tmax"].mean()

fig = px.line(
    daily,
    x="date",
    y="tmax",
    markers=True,
    title=f"Temperature Trend: {region}",
    labels={
        "date": "Date",
        "tmax": "Average Tmax (°C)"
    }
)

fig.add_hline(
    y=threshold,
    line_dash="dash",
    annotation_text="Selected threshold"
)

st.plotly_chart(fig, use_container_width=True)

# Chart 2: Temperature distribution
fig2 = px.histogram(
    result,
    x="tmax",
    nbins=25,
    title="Temperature Distribution",
    labels={"tmax": "Maximum temperature (°C)"}
)

st.plotly_chart(fig2, use_container_width=True)

# Chart 3: Compare all regions during the date range
period = df[
    (df["date"].dt.date >= start) &
    (df["date"].dt.date <= end)
]

summary = period.groupby(
    "region", as_index=False
)["tmax"].mean()

summary = summary.sort_values(
    "tmax", ascending=False
)

fig3 = px.bar(
    summary,
    x="region",
    y="tmax",
    title="Average Maximum Temperature by Region",
    labels={
        "region": "Region",
        "tmax": "Average Tmax (°C)"
    }
)

st.plotly_chart(fig3, use_container_width=True)

st.subheader("Temperature Records")
st.dataframe(result, use_container_width=True)

st.download_button(
    "Download CSV",
    result.to_csv(index=False).encode("utf-8"),
    file_name="heatwave_results.csv",
    mime="text/csv"
)
