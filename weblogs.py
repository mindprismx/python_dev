# weblogs_dashboard.py
"""
Streamlit weblogs dashboard - defaults to most recent full day under /home/dave/logs/http_access/
Supports: Last full day (default), Last 24 hours, Last 7 days, Last 30 days, Custom range.
"""
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
import pathlib
import glob
import re

import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(layout="wide", page_title="Weblogs Dashboard")

# ---------- CONFIG ----------
DEFAULT_BASE = "/home/dave/logs/http_access"
LOCAL_TZ = ZoneInfo("America/Chicago")
UTC = ZoneInfo("UTC")
# ----------------------------

base_dir = st.text_input("Logs base dir", DEFAULT_BASE)

if not base_dir:
    st.stop()

pbase = pathlib.Path(base_dir)
if not pbase.exists():
    st.error(f"Path does not exist: {base_dir}")
    st.stop()

# --- helpers to infer day (YYYY-MM-DD) from a file path or filename ---
date_pattern_in_name = re.compile(r"(\d{8})T(\d{6})")  # e.g. 20250831T235238

def infer_date_from_path(path: pathlib.Path):
    parts = path.parts
    # look for YYYY / MM / DD sequence in the path
    for i in range(len(parts) - 2):
        y, m, d = parts[i], parts[i + 1], parts[i + 2]
        if len(y) == 4 and y.isdigit() and len(m) == 2 and m.isdigit() and len(d) == 2 and d.isdigit():
            try:
                return date(int(y), int(m), int(d))
            except Exception:
                pass
    # fallback: try to extract timestamp from filename
    m = date_pattern_in_name.search(path.name)
    if m:
        ymd = m.group(1)  # YYYYMMDD
        try:
            return date(int(ymd[0:4]), int(ymd[4:6]), int(ymd[6:8]))
        except Exception:
            pass
    # last resort: file's mtime (local)
    try:
        ts = datetime.fromtimestamp(path.stat().st_mtime, LOCAL_TZ)
        return ts.date()
    except Exception:
        return None

# --- scan for available day directories (based on files present) ---
@st.cache_data(show_spinner=False)
def discover_days(base: str):
    found = set()
    for f in pathlib.Path(base).rglob("*.ndjson"):
        d = infer_date_from_path(f)
        if d:
            found.add(d)
    return sorted(found)

with st.spinner("Scanning log tree for available days..."):
    available_days = discover_days(base_dir)

if not available_days:
    st.warning("No ndjson files found under that path.")
    st.stop()

# choose default: the latest day that is strictly < today (local). If none, choose max available.
today_local = datetime.now(LOCAL_TZ).date()
past_days = [d for d in available_days if d < today_local]
if past_days:
    default_day = max(past_days)
else:
    default_day = max(available_days)

# --- Time range selection UI ---
st.sidebar.header("Time range")
preset = st.sidebar.radio("Preset", ("Last full day (default)", "Last 24 hours", "Last 7 days", "Last 30 days", "Custom range"))

if preset == "Last full day (default)":
    # start = local midnight of default_day, end = next local midnight
    start_local = datetime.combine(default_day, time.min, tzinfo=LOCAL_TZ)
    end_local = start_local + timedelta(days=1)
elif preset == "Last 24 hours":
    end_local = datetime.now(LOCAL_TZ)
    start_local = end_local - timedelta(days=1)
elif preset == "Last 7 days":
    end_local = datetime.now(LOCAL_TZ)
    start_local = end_local - timedelta(days=7)
elif preset == "Last 30 days":
    end_local = datetime.now(LOCAL_TZ)
    start_local = end_local - timedelta(days=30)
else:  # custom
    # show date pickers (local dates)
    cd1 = st.sidebar.date_input("Start date (local)", default_day - timedelta(days=1))
    cd2 = st.sidebar.date_input("End date (local, inclusive)", default_day)
    # interpret start at midnight local, end at midnight of day after cd2 (exclusive)
    start_local = datetime.combine(cd1, time.min, tzinfo=LOCAL_TZ)
    end_local = datetime.combine(cd2, time.min, tzinfo=LOCAL_TZ) + timedelta(days=1)

# convert to UTC for filtering against ts in logs (which are UTC 'Z')
start_utc = start_local.astimezone(UTC)
end_utc = end_local.astimezone(UTC)

st.sidebar.write(f"Filtering UTC: {start_utc.isoformat()} — {end_utc.isoformat()}")
st.markdown(f"### Showing logs from **{start_local.date().isoformat()}** (local) — range:\n`{start_utc.isoformat()}` →\n`{end_utc.isoformat()}` (UTC)")

# --- pick which days to include by comparing file-inferred dates to the date range ---
def files_for_range(base: str, start_local_dt: datetime, end_local_dt: datetime):
    # select files whose inferred date is between start_local.date() and end_local.date() (inclusive for dates)
    start_date = start_local_dt.date()
    end_date = (end_local_dt - timedelta(seconds=1)).date()  # inclusive last date
    selected_files = []
    for f in pathlib.Path(base).rglob("*.ndjson"):
        d = infer_date_from_path(f)
        if not d:
            continue
        if start_date <= d <= end_date:
            selected_files.append(str(f))
    return sorted(selected_files)

with st.spinner("Finding log files for the selected range..."):
    files = files_for_range(base_dir, start_local, end_local)

st.write(f"Found **{len(files):,}** ndjson files in range (will load and filter by `ts` afterward).")

if not files:
    st.warning("No files matched the selected date range.")
    st.stop()

# --- load ndjson files (cached) and filter by UTC timestamp ---
@st.cache_data(show_spinner=False)
def load_and_filter(file_list, start_utc_iso, end_utc_iso):
    dfs = []
    s = pd.to_datetime(start_utc_iso)
    e = pd.to_datetime(end_utc_iso)
    for f in file_list:
        try:
            d = pd.read_json(f, lines=True)
            dfs.append(d)
        except Exception:
            # skip malformed files
            continue
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    # normalize ts
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
        df = df[(df["ts"] >= s) & (df["ts"] < e)]
    else:
        # if no ts field, return as-is (user will get whole set)
        pass
    return df

with st.spinner("Loading and filtering logs (this may take a moment)..."):
    df = load_and_filter(files, start_utc.isoformat(), end_utc.isoformat())

if df.empty:
    st.error("No rows after filtering by ts. Check timestamps or selected range.")
    st.stop()

# --- Header metrics ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Start (first ts)", df["ts"].min().strftime("%Y-%m-%d %H:%M:%S") if "ts" in df.columns else "n/a")
c3.metric("End (last ts)", df["ts"].max().strftime("%Y-%m-%d %H:%M:%S") if "ts" in df.columns else "n/a")
c4.metric("Unique IPs", df["ip"].nunique() if "ip" in df.columns else "n/a")

# --- field exploration panels ---
st.subheader("Field value counts")
default_fields = ["path", "ip", "status", "method", "country", "ref", "query"]
available_fields = list(df.columns)
fields = st.multiselect("Fields to analyze", options=available_fields, default=[f for f in default_fields if f in available_fields])

if fields:
    tabs = st.tabs(fields)
    for fld, tab in zip(fields, tabs):
        with tab:
            vc = df[fld].fillna("<NULL>").astype(str).value_counts().rename_axis(fld).reset_index(name="count")
            st.dataframe(vc.head(200), use_container_width=True)
            if vc.shape[0] > 1:
                chart = alt.Chart(vc.head(50)).mark_bar().encode(
                    x=alt.X("count:Q"),
                    y=alt.Y(f"{fld}:N", sort='-x')
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)

# --- requests over time ---
if "ts" in df.columns:
    st.subheader("Requests over time")
    df_ts = df.set_index("ts").resample("5T").size().rename("requests").reset_index()
    line = alt.Chart(df_ts).mark_line().encode(x="ts:T", y="requests:Q").properties(height=240)
    st.altair_chart(line, use_container_width=True)

# --- raw rows with basic filters ---
st.subheader("Raw rows (preview + filters)")
q_status = st.multiselect("Status filter", options=sorted(df["status"].astype(str).unique()) if "status" in df.columns else [], default=[])
q_ip = st.text_input("Filter IP (substring)")

df_view = df
if q_status:
    df_view = df_view[df_view["status"].astype(str).isin(q_status)]
if q_ip:
    df_view = df_view[df_view["ip"].astype(str).str.contains(q_ip)]

st.dataframe(df_view.head(1000), use_container_width=True)

csv = df_view.to_csv(index=False)
st.download_button("Download filtered CSV", csv, file_name=f"weblogs-{start_local.date().isoformat()}_to_{(end_local - timedelta(days=1)).date().isoformat()}.csv")

st.caption("Performance tip: convert daily ndjson → parquet and query parquet for faster reloads. Next step: DuckDB for SQL over huge datasets.")
