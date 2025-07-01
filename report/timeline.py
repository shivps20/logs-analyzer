import streamlit as st
import altair as alt
import pandas as pd

def show_timeline_chart(_df):
    st.subheader("🕒 Timeline of Events by File (Grouped Line Chart)")
    # Exclude warnings
    _df = _df[_df["Type"].str.lower() != "warning"]
    if _df["Timestamp"].notna().any():
        timeline_df = _df.dropna(subset=["Timestamp"]).copy()
        if not timeline_df.empty:
            timeline_df["Minute"] = pd.to_datetime(timeline_df["Timestamp"]).dt.floor("min")
            files = sorted(timeline_df["Source File"].unique())
            # Multi-select to show/hide lines
            selected_files = st.multiselect(
                "Select log files to display:",
                files,
                default=files
            )
            if selected_files:
                filtered_df = timeline_df[timeline_df["Source File"].isin(selected_files)]
                grouped = (
                    filtered_df.groupby(["Minute", "Source File"])
                    .size()
                    .reset_index(name="Count")
                )
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
                st.info("Please select at least one log file to display.")
        else:
            st.info("No valid timestamps available to plot the timeline.")
    else:
        st.info("No valid timestamps available to plot the timeline.")