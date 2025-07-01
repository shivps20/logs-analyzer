import streamlit as st
import pandas as pd

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