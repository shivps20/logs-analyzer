import streamlit as st
import re


# def show_metrics_dashboard(df):
#     st.subheader("📊 Metrics Dashboard")
#     # Count total errors, warnings, exceptions per file
#     summary = (
#         df.groupby("Source File")["Type"]
#         .value_counts()
#         .unstack(fill_value=0)
#         .reset_index()
#     )
#     total_counts = df["Source File"].value_counts().to_dict()
#     cols = st.columns(len(summary["Source File"]))
#     for idx, row in summary.iterrows():
#         with cols[idx]:
#             # Smaller font for file name
#             st.markdown(f"<div style='font-size:13px; font-weight:bold; color:blue'>{row['Source File']}</div>", unsafe_allow_html=True)
            
#             # st.metric("File", row["Source File"])
#             for t in summary.columns[1:]:
#                 st.write(f"**{t}:** {row[t]}")
#             st.write(f"**Total:** {total_counts.get(row['Source File'], 0)}")    


def show_metrics_dashboard(df):
    st.subheader("📊 Metrics Dashboard")
    # Clean file names: remove extension and date
    def clean_filename(fname):
        # Remove extension
        fname = re.sub(r'\.[^.]+$', '', fname)
        # Remove date patterns like 2025-07-01 or 20250701 or similar
        fname = re.sub(r'[-_.]?\d{4}[-_.]?\d{2}[-_.]?\d{2}', '', fname)
        return fname

    df = df.copy()
    df["Source File"] = df["Source File"].apply(clean_filename)

    summary = (
        df.groupby(["Type", "Source File"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )
    # Add a "Total" row at the bottom for each file
    summary.loc["Total"] = summary.sum(axis=0)
    summary = summary.reset_index().rename(columns={"Type": "Error Type"})

    # Highlight the "Total" row with a background color
    def highlight_total_row(row):
        color = 'background-color: #ffe599' if row['Error Type'] == 'Total' else ''
        return [color] * len(row)

    # Show as a table
    st.dataframe(
        summary.style.apply(highlight_total_row, axis=1),
        use_container_width=True
    )