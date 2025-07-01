import pandas as pd
import streamlit as st
import altair as alt
from utils.constants import status_descriptions

"""
The show_request_volume function is designed to visualize the volume of requests over time, grouped by hour. 

If valid timestamps are present, the function creates a new column called 'hour' by formatting each timestamp to
 the year, month, day, and hour (e.g., '2024-06-10 14:00'). 
 
 This groups all requests that occurred within the same hour together. Using the Altair library, the function constructs a 
 bar chart where the x-axis represents each hour and the y-axis shows the count of requests for that hour. 
 
 Tooltips are added to display the hour and the corresponding request count when hovering over each bar. Finally, 
 the chart is rendered in the Streamlit app, set to automatically adjust its width to fit the container.

What: Shows how many requests your server received per hour.
Insight: Helps identify peak usage periods, traffic trends, and potential times of overload or inactivity
"""
def show_request_volume(df):
    st.markdown("### 📈Shows how many requests the Server received per hour.")
    if df['timestamp'].notnull().any():
        df['hour'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:00')
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('hour:N', title='Hour'),
            y=alt.Y('count()', title='Request Count'),
            tooltip=['hour', 'count()']
        ).properties(width=700)
        st.altair_chart(chart, use_container_width=True)


"""
The show_status_code_distribution function visualizes the distribution of HTTP status codes in a DataFrame.
Counts the occurrences of each unique status code using value_counts(). The result is reset to a new DataFrame 
with two columns, which are renamed to 'Status' and 'Count' for clarity

What: Pie chart and table showing the frequency of each HTTP status code (e.g., 200, 404, 500).
Insight: Reveals the proportion of successful requests vs. errors. A high number of 4xx/5xx codes may indicate client or server issues.
"""
def show_status_code_distribution(df):
    st.markdown("### 🛑  Frequency of each HTTP Status Code")

    status_counts = df['status'].dropna().astype(int).value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    status_counts['Status Description'] = status_counts['Status'].map(status_descriptions).fillna("Unknown")
    status_counts = status_counts[['Status', 'Status Description', 'Count']]
    if not status_counts.empty:
        st.dataframe(status_counts)

        # To show the distribution of status codes, using a pie chart
        # pie = alt.Chart(status_counts).mark_arc().encode(
        #     theta=alt.Theta(field="Count", type="quantitative"),
        #     color=alt.Color(field="Status", type="nominal"),
        #     tooltip=['Status', 'Count']
        # )
        # st.altair_chart(pie, use_container_width=True)

"""
The show_top_urls function displays the top 10 requested URLs from a DataFrame.
It checks if the 'url' column exists, counts the occurrences of each URL using value_counts

What: Table and bar chart of the most frequently accessed endpoints.
Insight: Identifies your most popular resources/APIs and can highlight hot spots or potential abuse.
"""
def show_top_urls(df):
    st.markdown("### 🔥 Top 10 Requested URLs")
    if 'url' in df.columns:
        url_counts = df['url'].value_counts().head(10).reset_index()
        url_counts.columns = ['URL', 'Count']
        st.dataframe(url_counts)
        bar = alt.Chart(url_counts).mark_bar().encode(
            x=alt.X('Count:Q'),
            y=alt.Y('URL:N', sort='-x'),
            tooltip=['URL', 'Count']
        )
        # st.altair_chart(bar, use_container_width=True)

"""
The show_top_ips function visualizes the top 10 IP addresses by request count from a DataFrame.
It counts the occurrences of each IP address using value_counts(), resets the index to create a new

The function calculates the frequency of each IP address in the 'ip' column using the value_counts() method, 
selects the top 10 most frequent IPs with head(10), and resets the index to create a new DataFrame.

What: Table and bar chart of the IP addresses making the most requests.
Insight: Shows your most active clients, possible bots, or sources of suspicious activity.
"""
# def show_top_ips(df):
#     st.markdown("### 🌐 IP addresses making the most Requests")
#     ip_counts = df['ip'].value_counts().head(10).reset_index()
#     ip_counts.columns = ['IP', 'Count']
#     st.dataframe(ip_counts)
#     bar = alt.Chart(ip_counts).mark_bar().encode(
#         x=alt.X('Count:Q'),
#         y=alt.Y('IP:N', sort='-x'),
#         tooltip=['IP', 'Count']
#     )
    # st.altair_chart(bar, use_container_width=True)

# @st.cache_data(show_spinner=False)
# def get_ip_requests(df, ip):
#     ip_df = df[df['ip'] == ip][['timestamp', 'url']].sort_values('timestamp')
#     ip_df = ip_df.rename(columns={'timestamp': 'Time', 'url': 'URL'})
#     return ip_df

@st.cache_data(show_spinner=False)
def get_top_ip_requests_map(df, top_n=10):
    # Precompute and cache all requests for the top N IPs
    ip_counts = df['ip'].value_counts().head(top_n).index.tolist()
    ip_requests_map = {}
    for ip in ip_counts:
        ip_df = df[df['ip'] == ip][['timestamp', 'url']].sort_values('timestamp')
        ip_df = ip_df.rename(columns={'timestamp': 'Time', 'url': 'URL'})
        ip_requests_map[ip] = ip_df
    return ip_requests_map

def show_top_ips_with_details(df):
    st.markdown("### 🌐 IP addresses making the most Requests (click IP for details)")
    ip_counts = df['ip'].value_counts().head(10).reset_index()
    ip_counts.columns = ['IP', 'Count']

    ip_requests_map = get_top_ip_requests_map(df, top_n=10)

    if 'open_ip' not in st.session_state:
        st.session_state.open_ip = None

    # Render the list of IPs with "Show" buttons
    for idx, row in ip_counts.iterrows():
        ip = row['IP']
        count = row['Count']
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button(f"Show {ip}", key=f"show_ip_{ip}"):
                st.session_state.open_ip = ip
        with col2:
            st.write(count)

    # Render the popup/details for the selected IP only, outside the loop
    open_ip = st.session_state.open_ip

    # Handle close action before rendering details
    if open_ip:
        if st.button("Close", key="close_ip"):
            st.session_state.open_ip = None
            open_ip = None  # Immediately update local variable

    if open_ip:
        st.markdown(f"#### Requests from IP: {open_ip}")
        ip_df = ip_requests_map.get(open_ip)
        st.dataframe(ip_df, use_container_width=True)

"""
What: Table and bar chart of TLS versions and cipher suites used.
Insight: Ensures secure protocols are being used and helps detect outdated or insecure connections.
"""
def show_tls_usage(df):
    if 'protocol' in df.columns and df['protocol'].notnull().any():
        st.markdown("### 🔐 TLS Version & Cipher Suite Usage")
        tls_counts = df.groupby(['protocol', 'cipher']).size().reset_index(name='Count')
        st.dataframe(tls_counts)
        bar = alt.Chart(tls_counts).mark_bar().encode(
            x=alt.X('Count:Q'),
            y=alt.Y('cipher:N', sort='-x'),
            color='protocol:N',
            tooltip=['protocol', 'cipher', 'Count']
        )
        st.altair_chart(bar, use_container_width=True)

"""
The show_method_distribution function visualizes the distribution of HTTP methods (GET, POST, etc.) in a DataFrame.

What: Pie chart and table of HTTP methods (GET, POST, etc.).
Insight: Shows the usage pattern of your API (read vs. write operations) and can help spot unusual method usage.
"""
def show_method_distribution(df):
    st.markdown("### 🗂 Method Distribution")
    method_counts = df['method'].value_counts().reset_index()
    method_counts.columns = ['Method', 'Count']
    st.dataframe(method_counts)
    pie = alt.Chart(method_counts).mark_arc().encode(
        theta=alt.Theta(field="Count", type="quantitative"),
        color=alt.Color(field="Method", type="nominal"),
        tooltip=['Method', 'Count']
    )
    # st.altair_chart(pie, use_container_width=True)


"""
The show_large_small_responses function displays the largest and smallest responses from a DataFrame.

What: Tables of requests with the largest and smallest response sizes.
Insight: Helps detect unusually large downloads (potential data leaks or heavy resources) and 
empty/small responses (potential errors or misconfigurations).
"""
def show_large_small_responses(df):
    st.markdown("### 📦 Large/Small Response Sizes (KB)")
    st.write("**All sizes are in kilobytes (KB).**")
    columns = ['url', 'size']
    # Add more columns if they exist
    for col in ['filename', 'ip', 'timestamp', 'method', 'status', 'user_agent', 'referer', 'response_time']:
        if col in df.columns:
            columns.insert(0 if col == 'filename' else len(columns), col)
    # Convert size to KB for display (rounded to 2 decimals)
    df = df.copy()
    df['size_kb'] = (df['size'] / 1024).round(2)
    columns_display = [col if col != 'size' else 'size_kb' for col in columns]
    st.markdown("#### Top 20 Largest Responses")
    largest = df[columns_display].sort_values('size_kb', ascending=False).head(20).reset_index().rename(
        columns={
            'index': 'Row', 'url': 'URL', 'size_kb': 'Size (KB)', 'ip': 'IP', 'timestamp': 'Timestamp',
            'method': 'Method', 'status': 'Status', 'filename': 'Filename',
            'user_agent': 'User Agent', 'referer': 'Referer', 'response_time': 'Response Time'
        }
    )
    st.dataframe(largest, use_container_width=True)
    st.markdown("#### Top 10 Smallest Responses")
    smallest = df[columns_display].sort_values('size_kb', ascending=True).head(10).reset_index().rename(
        columns={
            'index': 'Row', 'url': 'URL', 'size_kb': 'Size (KB)', 'ip': 'IP', 'timestamp': 'Timestamp',
            'method': 'Method', 'status': 'Status', 'filename': 'Filename',
            'user_agent': 'User Agent', 'referer': 'Referer', 'response_time': 'Response Time'
        }
    )
    st.dataframe(smallest, use_container_width=True)

"""
The show_top_urls_over_time function displays the top 5 URLs over time, with a focus on hourly trends. 

It first determines the top 5 URLs with the most requests. Then, for the selected URLs, it groups the data by hour 
and counts the number of requests for each URL in that hour. The result is a time-series representation of request 
volumes for the top URLs. A line chart is used to visualize this data, with each line representing a URL and 
showing how its request volume changes over time. The chart provides insights into the popularity and usage trends 
of the top URLs, highlighting any potential patterns or anomalies.

What: Line chart of request trends for the top 5 URLs.
Insight: Understand the usage pattern of your top resources over time. Spot trends, peaks, and potential issues.
"""
def show_top_urls_over_time(df):
    st.markdown("### 📈 Top 5 URLs Over Time")
    if 'url' in df.columns and 'timestamp' in df.columns:
        # Ensure timestamp is datetime
        df = df[df['timestamp'].notnull()].copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        # Find top 5 URLs overall
        top_urls = df['url'].value_counts().head(5).index.tolist()
        df_top = df[df['url'].isin(top_urls)].copy()
        # Group by hour and url
        df_top['hour'] = df_top['timestamp'].dt.strftime('%Y-%m-%d %H:00')
        url_time_counts = df_top.groupby(['hour', 'url']).size().reset_index(name='Count')
        # Line chart
        chart = alt.Chart(url_time_counts).mark_line(point=True).encode(
            x=alt.X('hour:N', title='Hour', sort='ascending'),
            y=alt.Y('Count:Q', title='Request Count'),
            color=alt.Color('url:N', title='URL'),
            tooltip=['hour', 'url', 'Count']
        ).properties(width=700)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Required columns 'url' and 'timestamp' not found in the data.")

"""
The show_top_ips_over_time function displays the top 6 IPs over time, with a focus on hourly trends. 

It first determines the top 6 IPs with the most requests. Then, for the selected IPs, it groups the data by hour 
and counts the number of requests for each IP in that hour. The result is a time-series representation of request 
volumes for the top IPs. A line chart is used to visualize this data, with each line representing an IP and 
showing how its request volume changes over time. The chart provides insights into the activity and usage trends 
of the top IPs, highlighting any potential patterns or anomalies.

What: Line chart of request trends for the top 6 IPs.
Insight: Understand the usage pattern of your top clients over time. Spot trends, peaks, and potential issues.
"""
def show_top_ips_over_time(df):
    st.markdown("### 📈 Top 6 IPs Over Time")
    if 'ip' in df.columns and 'timestamp' in df.columns:
        # Ensure timestamp is datetime
        df = df[df['timestamp'].notnull()].copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        # Find top 6 IPs overall
        top_ips = df['ip'].value_counts().head(6).index.tolist()
        df_top = df[df['ip'].isin(top_ips)].copy()
        # Group by hour and ip
        df_top['hour'] = df_top['timestamp'].dt.strftime('%Y-%m-%d %H:00')
        ip_time_counts = df_top.groupby(['hour', 'ip']).size().reset_index(name='Count')
        # Line chart
        chart = alt.Chart(ip_time_counts).mark_line(point=True).encode(
            x=alt.X('hour:N', title='Hour', sort='ascending'),
            y=alt.Y('Count:Q', title='Request Count'),
            color=alt.Color('ip:N', title='IP'),
            tooltip=['hour', 'ip', 'Count']
        ).properties(width=700)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Required columns 'ip' and 'timestamp' not found in the data.")
