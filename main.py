import os
import random
from datetime import datetime

import pandas as pd
import streamlit as st

# -----------------------------
# Config
# -----------------------------
st.set_page_config(
    page_title="Smart-SOS Dashboard",
    page_icon="🛰️",
    layout="wide",
)

DATA_FILE = "iot_data.csv"
UPDATE_INTERVAL_SECONDS = 10  # 10 seconds

st.title("🛰️ Smart-SOS Environment Monitoring Dashboard")
st.write(
    "This dashboard displays live readings from the Smart SOS device: "
    "**Temperature, Humidity, and Airflow**. "
    "Readings are captured every **10 seconds** and stored for historical analysis."
)

# -----------------------------
# Helpers for persistence
# -----------------------------
def load_data():
    """Load existing data from CSV if available."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
        return df
    else:
        return pd.DataFrame(
            columns=["timestamp", "temperature", "humidity", "airflow"]
        )

def save_data(df: pd.DataFrame):
    """Save data to CSV."""
    df.to_csv(DATA_FILE, index=False)

def generate_iot_reading():
    """Generate a single simulated sensor reading."""
    now = datetime.now()

    temperature = round(random.uniform(28.0, 32.0), 2)  # °C
    humidity = round(random.uniform(70.0, 95.0), 2)      # %
    airflow = round(random.uniform(0.6, 2.4), 2)         # m/s

    return {
        "timestamp": now,
        "temperature": temperature,
        "humidity": humidity,
        "airflow": airflow,
    }

# -----------------------------
# Load / init data
# -----------------------------
if "data" not in st.session_state:
    st.session_state.data = load_data()

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("Controls")

run_simulation = st.sidebar.checkbox("Run simulation (every 10 seconds)", value=True)

# Date filter for historic data
data = st.session_state.data.copy()
if not data.empty:
    min_date = data["timestamp"].min().date()
    max_date = data["timestamp"].max().date()
    date_range = st.sidebar.date_input(
        "Filter by date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
else:
    date_range = None

st.sidebar.markdown("---")
st.sidebar.write("Data is stored in `iot_data.csv` in the app folder.")

# -----------------------------
# Auto-refresh (every 10 seconds)
# -----------------------------
if run_simulation:
    # This will rerun the script every 10 seconds (if your Streamlit version supports autorefresh)
    st_autorefresh = getattr(st, "autorefresh", None)
    if st_autorefresh is not None:
        st_autorefresh(interval=UPDATE_INTERVAL_SECONDS * 1000, key="iot_autorefresh")

# -----------------------------
# On each run: maybe add a new row
# -----------------------------
if run_simulation:
    new_row = generate_iot_reading()
    st.session_state.data = pd.concat(
        [st.session_state.data, pd.DataFrame([new_row])],
        ignore_index=True,
    )
    # Persist to CSV
    save_data(st.session_state.data)

# Reload into local variable for display
data = st.session_state.data.copy()

# -----------------------------
# Apply date filter (for historic query)
# -----------------------------
if not data.empty and date_range is not None and len(date_range) == 2:
    start_date, end_date = date_range
    mask = (data["timestamp"].dt.date >= start_date) & (data["timestamp"].dt.date <= end_date)
    data = data.loc[mask]

# -----------------------------
# Display section
# -----------------------------
if not data.empty:
    # Latest values from (filtered) data
    latest = data.iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature (°C)", f"{latest['temperature']:.2f}")
    col2.metric("Humidity (%)", f"{latest['humidity']:.2f}")
    col3.metric("Airflow (m/s)", f"{latest['airflow']:.2f}")

    # --- Three separate line charts side-by-side ---
    st.subheader("Sensor Readings Over Time")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.caption("Temperature (°C)")
        temp_chart_data = data[["timestamp", "temperature"]].set_index("timestamp")
        st.line_chart(temp_chart_data)

    with c2:
        st.caption("Humidity (%)")
        hum_chart_data = data[["timestamp", "humidity"]].set_index("timestamp")
        st.line_chart(hum_chart_data)

    with c3:
        st.caption("Airflow (m/s)")
        airflow_chart_data = data[["timestamp", "airflow"]].set_index("timestamp")
        st.line_chart(airflow_chart_data)

    # Raw data table
    st.subheader("Data Table")
    st.dataframe(
        data.sort_values("timestamp", ascending=False).reset_index(drop=True),
        use_container_width=True,
    )

    # Download button
    st.download_button(
        label="Download filtered data as CSV",
        data=data.to_csv(index=False),
        file_name="iot_data_filtered.csv",
        mime="text/csv",
    )
else:
    st.info(
        "No data yet. Enable **Run simulation** in the sidebar to start generating readings."
    )
