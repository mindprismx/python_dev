#!/usr/bin/env python3

import requests
import re

url = "https://www.augros.org/wimipaqm.shtml"
response = requests.get(url)

match = re.search(
    r"(?:ADDR\s+(\d+\.\d+\.\d+\.\d+)<br>)?NAME\s*([a-zA-Z0-9_.-]*)\.?(?:<font.*?><b>([^<]+)</b>)?",
    response.text,
)

if match:
    ip = match.group(1)
    name = match.group(2)
    domain = match.group(3)
    print(ip, f"\t{domain}")
