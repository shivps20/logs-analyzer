import streamlit as st

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