# import pandas as pd
# import streamlit as st

# from data.cache import get_parsed_apache_df
# from report import apache_reports as reports  # Adjust path as needed

# def show_apache_access_log_dashboard(apache_files):
#     df = get_parsed_apache_df(apache_files)
#     if df.empty:
#         st.warning("No valid Apache access or SSL log entries found.")
#         return
#     st.success(f"Parsed {len(df)} log entries.")

#     reports.show_request_volume(df)
#     reports.show_status_code_distribution(df)
#     reports.show_top_urls(df)
#     reports.show_top_ips(df)
#     reports.show_tls_usage(df)
#     reports.show_method_distribution(df)
#     reports.show_large_small_responses(df)  # Optional, if implemented