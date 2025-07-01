import streamlit as st
from data.parser import parse_log_lines, parse_apache_logs, parse_openj9_thread_dump
import pandas as pd
import re

"""
The get_parsed_df function is designed to process a list of uploaded log files and return a single, 
combined pandas DataFrame containing parsed log information. 
It is decorated with @st.cache_data(show_spinner=False), which means Streamlit will cache the function’s 
output to avoid redundant computation when the same files are uploaded again, improving performance and 
user experience.

Inside the function, an empty list all_dfs is initialized to collect DataFrames generated from each file. 
The function iterates over each uploaded_file in the provided list. For each file, it reads the file’s contents, 
decodes them as UTF-8 (ignoring any decoding errors), and splits the content into individual lines. These lines, 
along with the lowercased file name, are passed to the parse_log_lines function, which parses the log lines and 
returns a DataFrame with structured log data.

If the resulting DataFrame from parse_log_lines is not empty, a new column "Source File" is added to indicate 
the origin of each log entry, and the DataFrame is appended to all_dfs. After all files are processed, if any 
DataFrames were collected, they are concatenated into a single DataFrame using pd.concat, with 
ignore_index=True to reset the index. If no valid log entries were found in any file, 
an empty DataFrame is returned.
"""
# For Server Logs
@st.cache_data(show_spinner=False)
def get_parsed_df(uploaded_files):
    all_dfs = []
    for uploaded_file in uploaded_files:
        lines = uploaded_file.read().decode("utf-8", errors="ignore").splitlines()
        df = parse_log_lines(lines, uploaded_file.name.lower())
        if not df.empty:
            df["Source File"] = uploaded_file.name
            all_dfs.append(df)
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()


# For Apache Logs
@st.cache_data(show_spinner=False)
def get_parsed_apache_df(uploaded_files):
    all_records = []
    for f in uploaded_files:
        content = f.read().decode("utf-8", errors="ignore")
        lines = content.strip().splitlines()
        all_records.extend(parse_apache_logs(lines))
    df = pd.DataFrame(all_records)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d/%b/%Y:%H:%M:%S %z', errors='coerce')
        df['status'] = pd.to_numeric(df['status'], errors='coerce')
        df['size'] = pd.to_numeric(df['size'], errors='coerce')
    return df




# For Thread Dumps
@st.cache_data(show_spinner=False)
def extract_thread_info(threads):
    lock_owners = {}
    thread_waiting_on = {}
    thread_stack_map = {}
    thread_states = {}
    thread_blocks = {}

    for thread in threads:
        thread_text = "\n".join(thread)
        thread_name_match = re.match(r'^\"([^\"]+)\"', thread[0])
        thread_name = thread_name_match.group(1) if thread_name_match else "Unknown"

        state_match = re.search(r'java\.lang\.Thread\.State:\s+(\w+)', thread_text)
        state = state_match.group(1) if state_match else "UNKNOWN"
        thread_states[thread_name] = state

        locked_objs = re.findall(r'- locked <([^>]+)>', thread_text)
        for obj in locked_objs:
            lock_owners[obj] = thread_name

        waiting_match = re.search(r'- waiting to lock <([^>]+)>', thread_text)
        if waiting_match:
            thread_waiting_on[thread_name] = waiting_match.group(1)

        top_method = "N/A"
        stack = []
        for line in thread:
            if line.strip().startswith("at "):
                stack.append(line.strip())
                if top_method == "N/A" and not any(pkg in line for pkg in ['java.', 'jdk.', 'sun.']):
                    top_method = line.strip()
        thread_stack_map[thread_name] = top_method
        thread_blocks[thread_name] = stack

    return thread_states, thread_waiting_on, lock_owners, thread_stack_map, thread_blocks




@st.cache_data(show_spinner=False)
def get_threads_by_state(thread_states, full_stack_map):
    state_map = {}
    for state in set(thread_states.values()):
        threads = []
        for thread_name, thread_state in thread_states.items():
            if thread_state == state:
                stack = full_stack_map.get(thread_name, [])
                if isinstance(stack, list):
                    stack_str = "\n".join([frame for frame in stack if isinstance(frame, str)])
                elif isinstance(stack, str):
                    stack_str = stack
                else:
                    stack_str = "N/A"
                threads.append((thread_name, stack_str))
        state_map[state] = threads
    return state_map