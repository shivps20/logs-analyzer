import streamlit as st

def show_top_recurring_messages(df, selected_file):
    st.subheader("📌 Top Recurring Messages")
    # Exclude warnings
    df = df[df["Type"].str.lower() != "warning"]
    if selected_file != "ALL":
        df = df[df["Source File"] == selected_file]
    top_messages = df.groupby(["Source File", "Type", "Code", "Message"]).size().reset_index(name="Count")
    st.dataframe(top_messages.sort_values("Count", ascending=False).head(10), use_container_width=True)
