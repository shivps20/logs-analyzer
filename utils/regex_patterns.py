import re

error_regex = re.compile(r"(Error|Warning|System Error|Notice|SEVERE|WARNING)\s+#?(\d+)?\s*(.*)", re.IGNORECASE)
exception_regex = re.compile(r"\b([a-zA-Z_][\w\.]+Exception)\b")
timestamp_regex = re.compile(r"(\d{2}-\w{3}-\d{4} \d{2}:\d{2}:\d{2}\.\d{3})")
mxtrace_ts_pattern = re.compile(r":([A-Z][a-z]{2} [A-Z][a-z]{2} +\d{1,2} \d{2}:\d{2}:\d{2} \d{4})")
apache_ts_pattern = re.compile(r"\[(\w{3} \w{3} +\d{1,2} \d{2}:\d{2}:\d{2}\.\d+ \d{4})\]")

APACHE_ACCESS_LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) \S+" (?P<status>\d{3}) (?P<size>\d+)'
)

APACHE_SSL_LOG_PATTERN = re.compile(
    r'\[(?P<timestamp>[^\]]+)\] (?P<ip>\S+) (?P<tlsver>TLSv[0-9.]+) (?P<cipher>\S+) "(?P<method>\S+) (?P<url>\S+) \S+" (?P<size>\d+)'
)