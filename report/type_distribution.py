import streamlit as st
import altair as alt
import pandas as pd

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
