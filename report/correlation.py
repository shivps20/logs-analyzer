import streamlit as st
import os
import re

def get_time_options(df, selected_file, selected_date):
    times = (
        df[
            (df["Source File"] == selected_file) & (df["Date"].astype(str) == selected_date)
        ]["Time"]
        .astype(str)
        .apply(lambda t: t[:5] if t not in ["NaT", "None", ""] else None)
        .dropna()
        .unique()
    )
    return sorted([t for t in times if t and t != "NaT" and t != "None"])

def filter_df_by_range(df, selected_date, selected_times):
    def time_hhmm(t):
        t = str(t)
        return t[:5] if t not in ["NaT", "None", ""] else None
    return df[
        (df["Date"].astype(str) == selected_date)
        & (df["Time"].apply(time_hhmm).isin(selected_times))
    ]

def build_error_matrix(filtered, all_error_types, all_files):
    matrix = (
        filtered.groupby(["Type", "Source File"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=all_error_types, columns=all_files, fill_value=0)
        .reset_index()
    )
    matrix = matrix.set_index("Type")
    matrix = matrix.reindex(sorted(matrix.index), fill_value=0)
    return matrix

def _short_file_display_name(filename):
    # Remove extension
    name = os.path.splitext(filename)[0]
    # Remove date patterns like YYYY-MM-DD or YYYY_MM_DD or YYYYMMDD
    name = re.sub(r'[_\-\.]?\d{4}[_\-\.]?\d{2}[_\-\.]?\d{2}', '', name)
    name = re.sub(r'[_\-\.]?\d{8}', '', name)
    # Remove trailing underscores, dashes, or dots
    name = re.sub(r'[_\-\.]+$', '', name)
    return name

def render_matrix_with_links(matrix, all_files, start_time, end_time, selected_date):
    st.write(
        "<b>Rows:</b> Error Type &nbsp;&nbsp; <b>Columns:</b> All loaded files<br>"
        "<b>Values:</b> Total errors for each type in each file (in selected date/time range)",
        unsafe_allow_html=True
    )

    # Render header row with file names (shortened)
    header_cols = st.columns([2] + [1]*len(all_files))
    header_cols[0].markdown("<div style='font-size:13px; font-weight:bold; color:#666;'>Error Type</div>", unsafe_allow_html=True)
    for idx, file in enumerate(all_files):
        short_name = _short_file_display_name(file)
        header_cols[idx+1].markdown(
            f"<div style='font-size:13px; font-weight:bold; color:#1a73e8; word-break:break-all'>{short_name}</div>",
            unsafe_allow_html=True
        )

    # Render matrix rows (unchanged)
    for error_type in matrix.index:
        cols = st.columns([2] + [1]*len(all_files))
        cols[0].markdown(f"<div style='font-size:13px; font-weight:bold'>{error_type}</div>", unsafe_allow_html=True)
        for idx, file in enumerate(all_files):
            count = matrix.loc[error_type, file]
            btn_key = f"show_{file}_{error_type}_{start_time}_{end_time}_{selected_date}"
            if count > 0:
                if cols[idx+1].button(f"{count}", key=btn_key, help=f"Show details for {error_type} in {file}", type="primary"):
                    st.session_state["show_details"] = (file, error_type, selected_date, start_time, end_time)
            else:
                cols[idx+1].markdown("<div style='color:#888; font-size:15px;'>0</div>", unsafe_allow_html=True)

def show_error_details_table(df, file, error_type, selected_date, selected_times):
    st.markdown(f"### Details for **{error_type}** in **{file}** ({selected_date} {selected_times[0]} - {selected_times[-1]})")
    def time_hhmm(t):
        t = str(t)
        return t[:5] if t not in ["NaT", "None", ""] else None
    filtered = df[
        (df["Source File"] == file)
        & (df["Type"] == error_type)
        & (df["Date"].astype(str) == selected_date)
        & (df["Time"].apply(time_hhmm).isin(selected_times))
    ]
    if filtered.empty:
        st.info("No errors found for this selection.")
        return
    st.dataframe(
        filtered[
            ["Source File", "Line", "Date", "Time", "Type", "Code", "Message", "Timestamp"]
        ],
        use_container_width=True
    )

def show_correlation_matrix(df):
    st.subheader("🔗 Error Correlation Matrix by File and Time Range")
    df = df[df["Type"].str.lower() != "warning"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_file = st.selectbox(
            "Select Reference File",
            options=sorted(df["Source File"].unique()),
            key="corr_file"
        )
    with col2:
        dates_for_file = df[df["Source File"] == selected_file]["Date"].dropna().astype(str).unique()
        selected_date = st.selectbox(
            "Select Reference Date",
            options=sorted(dates_for_file),
            key="corr_date"
        )

    times_for_file_date = get_time_options(df, selected_file, selected_date)
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

    start_idx = times_for_file_date.index(start_time)
    end_idx = times_for_file_date.index(end_time)
    if start_idx > end_idx:
        st.warning("Start Time must be before or equal to End Time.")
        return
    selected_times = times_for_file_date[start_idx:end_idx + 1]

    filtered = filter_df_by_range(df, selected_date, selected_times)
    if filtered.empty:
        st.info("No errors found for the selected date and time range.")
        return

    all_error_types = sorted(df["Type"].unique())
    all_files = sorted(df["Source File"].unique())
    matrix = build_error_matrix(filtered, all_error_types, all_files)

    render_matrix_with_links(matrix, all_files, start_time, end_time, selected_date)

    # Show details if a button was clicked
    if "show_details" in st.session_state:
        file, error_type, selected_date, start_time, end_time = st.session_state["show_details"]
        selected_times = times_for_file_date[
            times_for_file_date.index(start_time):times_for_file_date.index(end_time)+1
        ]
        show_error_details_table(df, file, error_type, selected_date, selected_times)
        # Optionally clear after showing
        del st.session_state["show_details"]