# Run your app with - streamlit run C:\Shiv\GitHub\logs-analyzer\logsAnalyzerApp.py

import streamlit as st
from config.settings import APP_TITLE
from data.parser import parse_openj9_thread_dump
from report.threadDump import show_thread_dump_dashboard
from ui.layout import show_title
from ui.widgets import file_uploader
from data.cache import extract_thread_info, get_parsed_df, get_parsed_apache_df

from report.metrics import show_metrics_dashboard
from report.errors_table import show_all_errors_table
from report.recurring import show_top_recurring_messages
from report.type_distribution import show_type_distribution
from report.timeline import show_timeline_chart
from report.type_filter import show_type_filter
from report.export import show_export
from report.correlation import show_correlation_matrix


from report import apache_reports as reports 

show_title()

tab1, tab2, tab3 = st.tabs(["3DEXPERIENCE Logs", "Apache Access Logs", "Thread Dump Analysis"])
with tab1:
    st.markdown("### Server/Mxtrace Logs Analysis")
    st.markdown("Upload your 3DEXPERIENCE log files to analyze errors, warnings, and exceptions.")
    # show_clear_all_files_button() 
    uploaded_files = file_uploader(key="3dx_files")

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


with tab2:
    st.markdown("### Apache SSL/Access Logs Analysis")
    st.markdown("Upload Apache SSL/Access Log Files")
    apache_files = file_uploader(key="apache_files")

    if apache_files:
        df = get_parsed_apache_df(apache_files)
        # show_apache_access_log_dashboard(apache_files)
        if df.empty:
            st.warning("No valid Apache access or SSL log entries found.")
        else:
            st.success(f"Parsed {len(df)} log entries.")
            reports.show_request_volume(df)
            reports.show_status_code_distribution(df)
            reports.show_top_urls(df)
            reports.show_top_urls_over_time(df)
            reports.show_top_ips_with_details(df)
            reports.show_top_ips_over_time(df)
            reports.show_tls_usage(df)
            reports.show_method_distribution(df)
            reports.show_large_small_responses(df)  # Optional, if implemented        


with tab3:
    st.markdown("### Thread Dump Analysis")
    st.markdown("Upload Thread Dump Files")
    thread_dump_files = file_uploader(key="thread_dump_files")

    if thread_dump_files:
        for file in thread_dump_files:
            content = file.read().decode("utf-8", errors="ignore")
            threads = parse_openj9_thread_dump(content)
            if not threads:
                st.warning(f"No valid Dump entries found in {file.name}.")
            else:
                st.success(f"Parsed {len(threads)} thread entries from {file.name}.")
                thread_states, thread_waiting_on, lock_owners, stack_map, full_stack_map = extract_thread_info(threads)
                show_thread_dump_dashboard(thread_states, thread_waiting_on, lock_owners, stack_map, full_stack_map)
