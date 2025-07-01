# streamlit run C:\Shiv\GitHub\logs-analyzer\logs_dashboard.py

import streamlit as st
import pandas as pd
import re
from datetime import datetime
import altair as alt

# --- Regex Patterns ---
error_regex = re.compile(r"(Error|Warning|System Error|Notice|SEVERE|WARNING)\s+#?(\d+)?\s*(.*)", re.IGNORECASE)
exception_regex = re.compile(r"\b([a-zA-Z_][\w\.]+Exception)\b")
timestamp_regex = re.compile(r"(\d{2}-\w{3}-\d{4} \d{2}:\d{2}:\d{2}\.\d{3})")
mxtrace_ts_pattern = re.compile(r":([A-Z][a-z]{2} [A-Z][a-z]{2} +\d{1,2} \d{2}:\d{2}:\d{2} \d{4})")
apache_ts_pattern = re.compile(r"\[(\w{3} \w{3} +\d{1,2} \d{2}:\d{2}:\d{2}\.\d+ \d{4})\]")

# --- Streamlit Page Config ---
st.set_page_config(page_title="Logs Analyzer", layout="wide")
st.title("📊 3DEXPERIENCE Log Analysis Dashboard")

# --- Log Parsing ---
def parse_log_lines(lines, filename):
    results = []
    last_ts = None
    last_date = None
    last_time = None

    # Use global regex patterns
    global error_regex, exception_regex, timestamp_regex, mxtrace_ts_pattern, apache_ts_pattern

    for i, line in enumerate(lines):
        # --- mxtrace ---
        if filename.startswith("mxtrace"):
            header_match = mxtrace_ts_pattern.search(line)
            if header_match:
                try:
                    dt_str = header_match.group(1)
                    # Example: Jun 26 17:11:23 2025 or similar
                    # But our pattern is ":Jun Thu 26 17:11:23 2025"
                    # So we need to parse accordingly
                    # dt_str: 'Jun Thu 26 17:11:23 2025'
                    # Let's try to parse as "%b %a %d %H:%M:%S %Y" or "%a %b %d %H:%M:%S %Y"
                    try:
                        last_ts = datetime.strptime(dt_str, "%a %b %d %H:%M:%S %Y")
                    except Exception:
                        last_ts = datetime.strptime(dt_str, "%b %a %d %H:%M:%S %Y")
                    last_date = last_ts.date()
                    last_time = last_ts.time()
                except Exception:
                    last_ts = None
                    last_date = None
                    last_time = None
                continue  # Don't process header as error line

            # If this is an error/warning line, associate with last_ts
            if (err := error_regex.search(line)):
                err_type, code, msg = err.groups()
                results.append({
                    "Line": i + 1,
                    "Timestamp": last_ts,
                    "Date": last_date,
                    "Time": last_time,
                    "Type": err_type.strip(),
                    "Code": code if code else "N/A",
                    "Message": msg.strip()
                })
            elif (exc := exception_regex.search(line)):
                exception_name = exc.group(1)
                results.append({
                    "Line": i + 1,
                    "Timestamp": last_ts,
                    "Date": last_date,
                    "Time": last_time,
                    "Type": "Exception",
                    "Code": exception_name,
                    "Message": line.strip()
                })
            continue

        # --- stderr.log and similar ---
        # Try to extract timestamp from the line
        ts = None
        date = None
        time_ = None
        # Try all timestamp patterns
        if (m := timestamp_regex.search(line)):
            try:
                ts = datetime.strptime(m.group(1), "%d-%b-%Y %H:%M:%S.%f")
                date = ts.date()
                time_ = ts.time()
            except Exception:
                pass
        elif (m := apache_ts_pattern.search(line)):
            try:
                ts = datetime.strptime(m.group(1), "%a %b %d %H:%M:%S.%f %Y")
                date = ts.date()
                time_ = ts.time()
            except Exception:
                pass

        # If found, update last_ts
        if ts:
            last_ts = ts
            last_date = date
            last_time = time_

        # If this is an error/warning line, associate with last_ts
        if (err := error_regex.search(line)):
            err_type, code, msg = err.groups()
            results.append({
                "Line": i + 1,
                "Timestamp": last_ts,
                "Date": last_date,
                "Time": last_time,
                "Type": err_type.strip(),
                "Code": code if code else "N/A",
                "Message": msg.strip()
            })
        elif (exc := exception_regex.search(line)):
            exception_name = exc.group(1)
            results.append({
                "Line": i + 1,
                "Timestamp": last_ts,
                "Date": last_date,
                "Time": last_time,
                "Type": "Exception",
                "Code": exception_name,
                "Message": line.strip()
            })

    df = pd.DataFrame(results)
    if not df.empty and "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df["Date"] = df["Timestamp"].dt.date
        df["Time"] = df["Timestamp"].dt.time

    required_columns = ["Line", "Date", "Time", "Type", "Code", "Message", "Timestamp"]
    df_cols = list(df.columns)
    if all(col in df_cols for col in required_columns):
        df = df[required_columns]
    return df



# --- Report Functions ---
def show_all_errors_table(df):
    st.subheader("🗂️ All Errors")

    # Checkbox to show/hide warnings
    show_warnings = st.checkbox("Show Warnings", value=False, key="show_warnings")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_file = st.selectbox(
            "Source File",
            options=["ALL"] + sorted(df["Source File"].unique()),
            index=0,
            key="all_errors_file"
        )
    with col2:
        selected_date = st.selectbox(
            "Date",
            options=["ALL"] + sorted(df["Date"].dropna().unique()),
            index=0,
            key="all_errors_date"
        )
    with col3:
        manual_time = st.text_input("Time (manual entry, e.g. 23:35 or 23:35:20)", value="", key="all_errors_time")
    with col4:
        selected_type = st.selectbox(
            "Type",
            options=["ALL"] + sorted(df["Type"].unique()),
            index=0,
            key="all_errors_type"
        )

    filtered_df = df.copy()

    # Only show warnings if checkbox is ticked
    if not show_warnings:
        filtered_df = filtered_df[filtered_df["Type"].str.lower() != "warning"]

    if selected_file != "ALL":
        filtered_df = filtered_df[filtered_df["Source File"] == selected_file]
    if selected_date != "ALL":
        filtered_df = filtered_df[filtered_df["Date"] == selected_date]
    if manual_time.strip():
        # Allow filtering by hh:mm or hh:mm:ss
        filtered_df = filtered_df[
            filtered_df["Time"].astype(str).str.startswith(manual_time.strip())
        ]
    if selected_type != "ALL":
        filtered_df = filtered_df[filtered_df["Type"] == selected_type]

    # Format Time column as string (hh:mm:ss) for display
    if not filtered_df.empty and "Time" in filtered_df.columns:
        filtered_df["Time"] = filtered_df["Time"].apply(
            lambda t: t.strftime("%H:%M:%S") if pd.notnull(t) and t is not None else ""
        )

    st.dataframe(
        filtered_df[
            ["Source File", "Line", "Date", "Time", "Type", "Code", "Message", "Timestamp"]
        ],
        use_container_width=True
    )
    # Return the selected file for use in Top Recurring Messages
    return selected_file, filtered_df



def show_top_recurring_messages(df, selected_file):
    st.subheader("📌 Top Recurring Messages")
    # Exclude warnings
    df = df[df["Type"].str.lower() != "warning"]
    if selected_file != "ALL":
        df = df[df["Source File"] == selected_file]
    top_messages = df.groupby(["Source File", "Type", "Code", "Message"]).size().reset_index(name="Count")
    st.dataframe(top_messages.sort_values("Count", ascending=False).head(10), use_container_width=True)




def show_type_distribution(_df):
    st.subheader("📈 Type Distribution by File (Grouped Bar Chart)")
    # Exclude warnings
    _df = _df[_df["Type"].str.lower() != "warning"]
    type_dist = _df.groupby(["Type", "Source File"]).size().reset_index(name="Count")

    if type_dist.empty:
        st.info("No error/warning/exception data available to display.")
        return

    # Ensure all combinations of Type and Source File are present (even if count is 0)
    all_types = sorted(_df["Type"].unique())
    all_files = sorted(_df["Source File"].unique())
    full_index = pd.MultiIndex.from_product([all_types, all_files], names=["Type", "Source File"])
    type_dist = type_dist.set_index(["Type", "Source File"]).reindex(full_index, fill_value=0).reset_index()

    # Altair grouped bar chart with labels
    chart = (
        alt.Chart(type_dist)
        .mark_bar()
        .encode(
            x=alt.X("Type:N", title="Error Type", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Count:Q", title="Count"),
            color=alt.Color("Source File:N", title="Log File"),
            xOffset="Source File:N",
            tooltip=["Type", "Source File", "Count"]
        )
        .properties(width=60 * len(all_files), height=400)
    )

    # Add text labels on top of bars
    text = (
        alt.Chart(type_dist)
        .mark_text(
            align="center",
            baseline="bottom",
            dy=-2,
            fontSize=12,
            fontWeight="bold"
        )
        .encode(
            x=alt.X("Type:N", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Count:Q"),
            xOffset="Source File:N",
            detail="Source File:N",
            text=alt.Text("Count:Q"),
            color=alt.value("black")
        )
    )

    st.altair_chart((chart + text).configure_axis(labelFontSize=12, titleFontSize=14), use_container_width=True)

def show_timeline_chart(_df):
    st.subheader("🕒 Timeline of Events by File (Grouped Line Chart)")
    # Exclude warnings
    _df = _df[_df["Type"].str.lower() != "warning"]
    if _df["Timestamp"].notna().any():
        timeline_df = _df.dropna(subset=["Timestamp"]).copy()
        if not timeline_df.empty:
            timeline_df["Minute"] = pd.to_datetime(timeline_df["Timestamp"]).dt.floor("min")
            # Count events per file per minute
            grouped = (
                timeline_df.groupby(["Minute", "Source File"])
                .size()
                .reset_index(name="Count")
            )
            # Altair multi-line chart, one line per file, with zoom/pan
            zoom = alt.selection_interval(bind='scales', encodings=['x', 'y'])
            chart = (
                alt.Chart(grouped)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Minute:T", title="Time (Minute)"),
                    y=alt.Y("Count:Q", title="Event Count"),
                    color=alt.Color("Source File:N", title="Log File"),
                    tooltip=["Minute", "Source File", "Count"]
                )
                .add_params(zoom)
                .properties(width=700, height=400)
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No valid timestamps available to plot the timeline.")
    else:
        st.info("No valid timestamps available to plot the timeline.")

def show_type_filter(filtered_df):
    st.subheader("🔍 Filter by Type or Exception")
    if filtered_df["Type"].nunique() > 0:
        col1, col2 = st.columns(2)
        with col1:
            selected_file = st.selectbox(
                "Select Source File",
                options=["ALL"] + sorted(filtered_df["Source File"].unique()),
                index=0
            )
        with col2:
            selected_type = st.selectbox(
                "Select Type",
                options=["ALL"] + sorted(filtered_df["Type"].unique()),
                index=0
            )

        df_filtered = filtered_df.copy()
        if selected_file != "ALL":
            df_filtered = df_filtered[df_filtered["Source File"] == selected_file]
        if selected_type != "ALL":
            df_filtered = df_filtered[df_filtered["Type"] == selected_type]

        st.dataframe(
            df_filtered[
                ["Source File", "Line", "Date", "Time", "Type", "Code", "Message", "Timestamp"]
            ],
            use_container_width=True
        )

def show_export(filtered_df):
    st.subheader("📥 Export")
    csv = filtered_df.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="log_summary.csv", mime="text/csv")

def show_metrics_dashboard(df):
    st.subheader("📊 Metrics Dashboard")
    # Count total errors, warnings, exceptions per file
    summary = (
        df.groupby("Source File")["Type"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    total_counts = df["Source File"].value_counts().to_dict()
    cols = st.columns(len(summary["Source File"]))
    for idx, row in summary.iterrows():
        with cols[idx]:
            st.metric("File", row["Source File"])
            for t in summary.columns[1:]:
                st.write(f"**{t}:** {row[t]}")
            st.write(f"**Total:** {total_counts.get(row['Source File'], 0)}")

def show_correlation_matrix(df):
    st.subheader("🔗 Error Correlation Matrix by File and Time Range")

    # Exclude warnings for correlation
    df = df[df["Type"].str.lower() != "warning"]

    # --- Step 1: File selection ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_file = st.selectbox(
            "Select Reference File",
            options=sorted(df["Source File"].unique()),
            key="corr_file"
        )

    # --- Step 2: Date selection (only dates from selected file) ---
    with col2:
        dates_for_file = df[df["Source File"] == selected_file]["Date"].dropna().astype(str).unique()
        selected_date = st.selectbox(
            "Select Reference Date",
            options=sorted(dates_for_file),
            key="corr_date"
        )

    # --- Step 3: Time selection (only times from selected file and date) ---
    # Get all times for the selected file and date, as hh:mm
    times_for_file_date = (
        df[
            (df["Source File"] == selected_file) & (df["Date"].astype(str) == selected_date)
        ]["Time"]
        .astype(str)
        .apply(lambda t: t[:5] if t not in ["NaT", "None", ""] else None)
        .dropna()
        .unique()
    )
    times_for_file_date = sorted([t for t in times_for_file_date if t and t != "NaT" and t != "None"])

    with col3:
        start_time = st.selectbox(
            "Start Time (hh:mm)",
            options=times_for_file_date,
            key="corr_start_time"
        ) if times_for_file_date else None

    with col4:
        end_time = st.selectbox(
            "End Time (hh:mm)",
            options=times_for_file_date,
            key="corr_end_time"
        ) if times_for_file_date else None

    if not (start_time and end_time):
        st.info("No valid times available for the selected file and date.")
        return

    # --- Step 4: Filter the DataFrame for the selected date and time range ---
    # Helper for time comparison
    def time_hhmm(t):
        t = str(t)
        return t[:5] if t not in ["NaT", "None", ""] else None

    # Ensure start_time <= end_time
    start_idx = times_for_file_date.index(start_time)
    end_idx = times_for_file_date.index(end_time)
    if start_idx > end_idx:
        st.warning("Start Time must be before or equal to End Time.")
        return
    selected_times = times_for_file_date[start_idx:end_idx + 1]

    # Filter for all files at the selected date and time range
    filtered = df[
        (df["Date"].astype(str) == selected_date)
        & (df["Time"].apply(time_hhmm).isin(selected_times))
    ]

    if filtered.empty:
        st.info("No errors found for the selected date and time range.")
        return

    # --- Step 5: Build the matrix ---
    # Get all error types (from all files, for this date/time range)
    all_error_types = sorted(df["Type"].unique())
    all_files = sorted(df["Source File"].unique())

    # Pivot: index=Type, columns=Source File, values=Count
    matrix = (
        filtered.groupby(["Type", "Source File"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=all_error_types, columns=all_files, fill_value=0)
        .reset_index()
    )

    matrix = matrix.set_index("Type")
    matrix = matrix.reindex(sorted(matrix.index), fill_value=0)

    st.write("**Rows:** Error Type &nbsp;&nbsp; **Columns:** All loaded files<br>**Values:** Total errors for each type in each file (in selected date/time range)", unsafe_allow_html=True)
    st.dataframe(matrix, use_container_width=True)



@st.cache_data(show_spinner=False)
def get_parsed_df(uploaded_files):
    all_dfs = []
    for uploaded_file in uploaded_files:
        lines = uploaded_file.read().decode("utf-8", errors="ignore").splitlines()
        df = parse_log_lines(lines, uploaded_file.name.lower())
        if not df.empty:
            df["Source File"] = uploaded_file.name
            all_dfs.append(df)
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()

# --- Main App Logic ---
uploaded_files = st.file_uploader(
    "📂 Upload one or more 3DEXPERIENCE Log Files (stderr.log / mxtrace.log / any)",
    type=["log", "txt"],
    accept_multiple_files=True
)

if uploaded_files:
    df = get_parsed_df(uploaded_files)
    if df.empty:
        st.warning("No recognizable errors, warnings, or exceptions found in any file.")
    else:
        st.success(f"✅ Parsed {len(df)} entries from {len(uploaded_files)} file(s).")
        show_metrics_dashboard(df)
        selected_file, filtered_df = show_all_errors_table(df)
        show_top_recurring_messages(df, selected_file)
        show_type_distribution(df)
        show_timeline_chart(df)
        show_type_filter(filtered_df)
        show_export(filtered_df)
        show_correlation_matrix(df)
