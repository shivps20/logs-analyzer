import pandas as pd
from datetime import datetime
from utils.regex_patterns import error_regex, exception_regex, timestamp_regex, mxtrace_ts_pattern, apache_ts_pattern
from utils.regex_patterns import APACHE_ACCESS_LOG_PATTERN, APACHE_SSL_LOG_PATTERN

def parse_log_lines(lines, filename):
    results = []
    last_ts = None
    last_date = None
    last_time = None

    # Use global regex patterns
    global error_regex, exception_regex, timestamp_regex, mxtrace_ts_pattern, apache_ts_pattern

    for i, line in enumerate(lines):
        # --- mxtrace ---
        if filename.startswith("mxtrace"):
            header_match = mxtrace_ts_pattern.search(line)
            if header_match:
                try:
                    dt_str = header_match.group(1)
                    # Example: Jun 26 17:11:23 2025 or similar
                    # But our pattern is ":Jun Thu 26 17:11:23 2025"
                    # So we need to parse accordingly
                    # dt_str: 'Jun Thu 26 17:11:23 2025'
                    # Let's try to parse as "%b %a %d %H:%M:%S %Y" or "%a %b %d %H:%M:%S %Y"
                    try:
                        last_ts = datetime.strptime(dt_str, "%a %b %d %H:%M:%S %Y")
                    except Exception:
                        last_ts = datetime.strptime(dt_str, "%b %a %d %H:%M:%S %Y")
                    last_date = last_ts.date()
                    last_time = last_ts.time()
                except Exception:
                    last_ts = None
                    last_date = None
                    last_time = None
                continue  # Don't process header as error line

            # If this is an error/warning line, associate with last_ts
            if (err := error_regex.search(line)):
                err_type, code, msg = err.groups()
                results.append({
                    "Line": i + 1,
                    "Timestamp": last_ts,
                    "Date": last_date,
                    "Time": last_time,
                    "Type": err_type.strip(),
                    "Code": code if code else "N/A",
                    "Message": msg.strip()
                })
            elif (exc := exception_regex.search(line)):
                exception_name = exc.group(1)
                results.append({
                    "Line": i + 1,
                    "Timestamp": last_ts,
                    "Date": last_date,
                    "Time": last_time,
                    "Type": "Exception",
                    "Code": exception_name,
                    "Message": line.strip()
                })
            continue

        # --- stderr.log and similar ---
        # Try to extract timestamp from the line
        ts = None
        date = None
        time_ = None
        # Try all timestamp patterns
        if (m := timestamp_regex.search(line)):
            try:
                ts = datetime.strptime(m.group(1), "%d-%b-%Y %H:%M:%S.%f")
                date = ts.date()
                time_ = ts.time()
            except Exception:
                pass
        elif (m := apache_ts_pattern.search(line)):
            try:
                ts = datetime.strptime(m.group(1), "%a %b %d %H:%M:%S.%f %Y")
                date = ts.date()
                time_ = ts.time()
            except Exception:
                pass

        # If found, update last_ts
        if ts:
            last_ts = ts
            last_date = date
            last_time = time_

        # If this is an error/warning line, associate with last_ts
        if (err := error_regex.search(line)):
            err_type, code, msg = err.groups()
            results.append({
                "Line": i + 1,
                "Timestamp": last_ts,
                "Date": last_date,
                "Time": last_time,
                "Type": err_type.strip(),
                "Code": code if code else "N/A",
                "Message": msg.strip()
            })
        elif (exc := exception_regex.search(line)):
            exception_name = exc.group(1)
            results.append({
                "Line": i + 1,
                "Timestamp": last_ts,
                "Date": last_date,
                "Time": last_time,
                "Type": "Exception",
                "Code": exception_name,
                "Message": line.strip()
            })

    df = pd.DataFrame(results)
    if not df.empty and "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df["Date"] = df["Timestamp"].dt.date
        df["Time"] = df["Timestamp"].dt.time

    required_columns = ["Line", "Date", "Time", "Type", "Code", "Message", "Timestamp"]
    df_cols = list(df.columns)
    if all(col in df_cols for col in required_columns):
        df = df[required_columns]
    return df


# Parse Apache access and SSL logs
def parse_apache_logs(lines):
    records = []
    for line in lines:
        # Try SSL log pattern first
        m_ssl = APACHE_SSL_LOG_PATTERN.match(line)
        if m_ssl:
            d = m_ssl.groupdict()
            d['status'] = None
            d['protocol'] = d.pop('tlsver')
            d['cipher'] = d['cipher']
            records.append(d)
            continue
        # Try access log pattern
        m_access = APACHE_ACCESS_LOG_PATTERN.match(line)
        if m_access:
            d = m_access.groupdict()
            d['protocol'] = None
            d['cipher'] = None
            records.append(d)
    return records


# Parse OpenJ9 thread dump format
def parse_openj9_thread_dump(content):
    threads = []
    current_thread = []
    for line in content.splitlines():
        if line.startswith('"') and current_thread:
            threads.append(current_thread)
            current_thread = []
        current_thread.append(line)
    if current_thread:
        threads.append(current_thread)
    return threads