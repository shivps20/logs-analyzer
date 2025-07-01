import streamlit as st

def show_export(filtered_df):
    st.subheader("📥 Export")
    csv = filtered_df.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="log_summary.csv", mime="text/csv")