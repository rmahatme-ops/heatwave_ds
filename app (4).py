import ctypes
import subprocess
from collections import deque
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "heatwave_data.csv"
C_SOURCE = BASE_DIR / "c" / "temperature_list.c"
C_LIBRARY = BASE_DIR / "c" / "temperature_list.so"


# ---------- Syllabus data structures implemented in Python ----------
class Stack:
    """LIFO stack implemented with a Python list."""
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop() if self.items else None

    def peek(self):
        return self.items[-1] if self.items else None


class Queue:
    """FIFO queue implemented with a deque."""
    def __init__(self):
        self.items = deque()

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        return self.items.popleft() if self.items else None

    def __len__(self):
        return len(self.items)


def load_data():
    if not CSV_PATH.exists():
        st.error("heatwave_data.csv was not found. Keep it in the same folder as app.py.")
        st.stop()

    data = pd.read_csv(CSV_PATH)
    required = {"region", "date", "lat", "lon", "tmax"}
    missing = required - set(data.columns)
    if missing:
        st.error(f"The CSV is missing required columns: {', '.join(sorted(missing))}")
        st.stop()

    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["tmax"] = pd.to_numeric(data["tmax"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data["lon"] = pd.to_numeric(data["lon"], errors="coerce")
    data = data.dropna(subset=["region", "date", "tmax"]).copy()
    data["region"] = data["region"].astype(str)
    data = data.sort_values(["date", "region"]).reset_index(drop=True)
    return data


def compile_c_library():
    """Compile the C linked-list implementation when a C compiler is available."""
    if not C_SOURCE.exists():
        return None, "C source file not found."
    try:
        result = subprocess.run(
            ["gcc", "-shared", "-fPIC", "-O2", str(C_SOURCE), "-o", str(C_LIBRARY)],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return None, result.stderr.strip() or "C compilation failed."
        lib = ctypes.CDLL(str(C_LIBRARY))
        double_array = ctypes.POINTER(ctypes.c_double)
        lib.analyze_temperatures.argtypes = [
            double_array, ctypes.c_int, ctypes.c_double,
            double_array, double_array, ctypes.POINTER(ctypes.c_int)
        ]
        lib.analyze_temperatures.restype = ctypes.c_int
        return lib, None
    except (OSError, FileNotFoundError) as exc:
        return None, str(exc)


def analyze_with_c(temperatures, threshold):
    """Pass a numeric array to C; return None if compilation/execution is unavailable."""
    lib, error = compile_c_library()
    if lib is None or len(temperatures) == 0:
        return None, error or "No valid temperatures to analyze."
    values = (ctypes.c_double * len(temperatures))(*[float(v) for v in temperatures])
    mean = ctypes.c_double(0.0)
    maximum = ctypes.c_double(0.0)
    heat_count = ctypes.c_int(0)
    status = lib.analyze_temperatures(
        values, len(temperatures), float(threshold),
        ctypes.byref(mean), ctypes.byref(maximum), ctypes.byref(heat_count)
    )
    if status != 0:
        return None, "The C function could not analyze this data."
    return {
        "count": len(temperatures),
        "mean": mean.value,
        "maximum": maximum.value,
        "heat_count": heat_count.value,
    }, None


st.set_page_config(page_title="Climate Intelligence", page_icon="🌡️", layout="wide")

st.title("🌡️ Climate Intelligence")
st.caption("Heatwave Monitoring • Data Structures IA-2 • KJS-CES-01")
st.write(
    "Explore historical maximum-temperature readings by IMD region and date. "
    "This is a historical-data dashboard, not an official forecast or emergency warning service."
)

data = load_data()
min_date = data["date"].min().date()
max_date = data["date"].max().date()

with st.sidebar:
    st.header("Dashboard filters")
    regions = sorted(data["region"].dropna().unique().tolist())
    selected_regions = st.multiselect("IMD region", regions, default=regions)
    date_range = st.date_input(
        "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )
    threshold = st.slider("Heat threshold (°C)", min_value=30.0, max_value=50.0, value=40.0, step=0.5)
    st.caption("Threshold is a configurable project setting, not an official IMD alert rule.")

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

filtered = data[
    data["region"].isin(selected_regions)
    & data["date"].dt.date.between(start_date, end_date)
].copy()

if filtered.empty:
    st.warning("No readings match these filters. Choose another region or date range.")
    st.stop()

daily = (
    filtered.groupby("date", as_index=False)
    .agg(mean_tmax=("tmax", "mean"), highest_tmax=("tmax", "max"), readings=("tmax", "size"))
)

mean_temp = float(filtered["tmax"].mean())
max_temp = float(filtered["tmax"].max())
heat_readings = int((filtered["tmax"] >= threshold).sum())
heat_days = int(filtered.loc[filtered["tmax"] >= threshold, "date"].nunique())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Temperature readings", f"{len(filtered):,}")
m2.metric("Mean Tmax", f"{mean_temp:.2f} °C")
m3.metric("Highest Tmax", f"{max_temp:.2f} °C")
m4.metric("Readings at/above threshold", f"{heat_readings:,}")

tab_overview, tab_structures, tab_data = st.tabs(
    ["Overview", "Data Structures Lab", "Filtered CSV Data"]
)

with tab_overview:
    st.subheader("Daily temperature trend")
    st.line_chart(daily.set_index("date")[["mean_tmax", "highest_tmax"]])
    st.caption("Mean Tmax and highest Tmax per date, calculated from the selected regions.")

    left, right = st.columns(2)
    with left:
        st.subheader("Readings by region")
        region_summary = (
            filtered.groupby("region", as_index=False)
            .agg(readings=("tmax", "size"), mean_tmax=("tmax", "mean"), max_tmax=("tmax", "max"))
            .sort_values("mean_tmax", ascending=False)
        )
        st.dataframe(region_summary.round(2), use_container_width=True, hide_index=True)
    with right:
        st.subheader("Threshold summary")
        st.write(f"- Configured threshold: **{threshold:.1f} °C**")
        st.write(f"- Readings at/above threshold: **{heat_readings:,}**")
        st.write(f"- Dates with at least one reading at/above threshold: **{heat_days:,}**")
        st.info("A date is counted once in the date total even if multiple grid points exceed the threshold.")

with tab_structures:
    st.subheader("C linked list: temperature analysis")
    st.write(
        "The C module creates a singly linked list using dynamic memory allocation. "
        "Each node stores one Tmax value and a pointer to the next node."
    )
    c_result, c_error = analyze_with_c(filtered["tmax"].to_numpy(dtype=float), threshold)
    if c_result:
        a, b, c, d = st.columns(4)
        a.metric("C node count", f'{c_result["count"]:,}')
        b.metric("C mean Tmax", f'{c_result["mean"]:.2f} °C')
        c.metric("C maximum Tmax", f'{c_result["maximum"]:.2f} °C')
        d.metric("C threshold readings", f'{c_result["heat_count"]:,}')
        st.success("C code compiled and ran successfully for the current filtered readings.")
    else:
        st.warning("The C shared library could not be run in this environment.")
        st.code(c_error or "Unknown compiler error")
        st.write("The dashboard still works with Python calculations. Install GCC to run the C module.")

    st.divider()
    st.subheader("Python stack (LIFO): most recent records")
    stack = Stack()
    recent = filtered.sort_values("date").tail(10)
    for record in recent.to_dict("records"):
        stack.push(record)
    stack_rows = []
    while stack.peek() is not None:
        item = stack.pop()
        stack_rows.append({
            "date": item["date"].date().isoformat(),
            "region": item["region"],
            "Tmax (°C)": round(float(item["tmax"]), 2),
        })
    st.write("Stack pop order: newest record first (Last In, First Out).")
    st.dataframe(pd.DataFrame(stack_rows), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Python queue (FIFO): heat-threshold review")
    queue = Queue()
    warning_rows = filtered[filtered["tmax"] >= threshold].sort_values("date").head(20)
    for record in warning_rows.to_dict("records"):
        queue.enqueue(record)
    queue_rows = []
    while len(queue):
        item = queue.dequeue()
        queue_rows.append({
            "date": item["date"].date().isoformat(),
            "region": item["region"],
            "Tmax (°C)": round(float(item["tmax"]), 2),
        })
    st.write("Queue dequeue order: earliest matching record first (First In, First Out).")
    if queue_rows:
        st.dataframe(pd.DataFrame(queue_rows), use_container_width=True, hide_index=True)
    else:
        st.write("No records meet the selected threshold.")

    st.divider()
    st.subheader("Map ADT / Dictionary")
    st.write(
        "Python dictionaries are used to represent grouped summaries by region, and the CSV's "
        "`region` field acts as the map key. The region summary above shows the values associated "
        "with each key."
    )

with tab_data:
    st.subheader("Filtered readings")
    st.write(f"Showing {len(filtered):,} rows from the selected region/date filters.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_heatwave_data.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "Dataset: heatwave_data.csv supplied with the project. Missing/invalid dates and Tmax values "
    "are excluded from calculations. This educational app does not replace official weather alerts."
)
