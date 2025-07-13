#!/usr/bin/env python3

import requests
import re

url = "https://www.augros.org/wimipaqm.shtml"
response = requests.get(url)

# print(response.status_code)  # 200 = OK
# print(response.text)  # HTML content

match = re.search(
    r"ADDR\s+(\d+\.\d+\.\d+\.\d+)<br>NAME\s+([a-zA-Z0-9_.-]+)\.<font color=blue><b>([^<]+)</b>",
    response.text,
)
if match:
    print(match.group(1), f"{match.group(2)}.{match.group(3)}")
