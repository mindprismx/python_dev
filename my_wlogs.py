#!/usr/bin/env python
# wlogs.py
# @spiralbend 2025-08-17

import os
import sys
import json
import subprocess

if "/home/dave/logs" in os.getcwd():
    root = os.getcwd()
else:
    root = "/home/dave/logs"

f_struct = {}
count = 0
member = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else "ip"
top = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else 20

for dirpath, dirnames, filenames in os.walk(root):
    for filename in filenames:
        file = dirpath + "/" + filename
        with open(file, "r") as fh:
            content = fh.read()
            data = json.loads(content)
            for field, key in data.items():
                if field not in f_struct:
                    f_struct[field] = {}
                f_struct[field][key] = f_struct[field].get(key, 0) + 1

for k, v in sorted(f_struct[member].items(), key=lambda x: x[1], reverse=True):
    print(f"{k}\t{v}")
    count += 1
    if count == top:
        break

# sample log
# {"ts":"2025-08-17T18:49:29.539Z",
#  "method":"GET",
#  "host":"augros.org",
#  "path":"/robots.txt",
#  "query":"",
#  "ip":"98.97.81.197",
#  "ua":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
#  "ref":"https://augros.org/",
#  "colo":"DFW",
#  "country":"US",
#  "asn":14593,
#  "status":200,
#  "cache":"REVALIDATED",
#  "ray":"970b5a06dd48f081",
#  "dur_ms":117}

# do ASN llokups with whois
# for k,v in sorted(f_struct['asn'].items(), key=lambda x: x[1], reverse=True):
#     org = subprocess.check_output(
#         f"whois -h whois.cymru.com ' -v AS{v}' | awk -F'|' 'NR==2 {{print $5}}'",
#         shell=True,
#         text=True
#     ).strip()
#     print(f"{org} ({k}):\t{v}")
#     count += 1
#     if count > top:
#         break
