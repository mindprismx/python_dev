#
# parse and profile network traffic using tcpdump
# @spiralbend 2025-06-27
#

import subprocess
import re
import sys

packets = int(sys.argv[1]) if len(sys.argv) > 1 else 100

sips = {}
spts = {}
dips = {}
dpts = {}

proc = subprocess.Popen(
    ["tcpdump", "-nntq", "-i", "wlp0s20f3", "-c", f"{packets}", "ip and not multicast"],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True  # str instead of bytes
)

for line in proc.stdout:
    match = re.search(r'(\d+\.\d+\.\d+\.\d+)\.(\d+)\s+>\s+(\d+\.\d+\.\d+\.\d+)\.(\d+):', line.strip())
    if match:
        src_ip, src_pt, dst_ip, dst_pt = match.groups()
        sips[src_ip] = sips.get(src_ip, 0) + 1
        spts[src_pt] = spts.get(src_pt, 0) + 1
        dips[dst_ip] = dips.get(dst_ip, 0) + 1
        dpts[dst_pt] = dpts.get(dst_pt, 0) + 1


def print_quadrants(sips, spts, dips, dpts, top_n=10):
    sips_items = sorted(sips.items(), key=lambda x: x[1], reverse=True)[:top_n]
    spts_items = sorted(spts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    dips_items = sorted(dips.items(), key=lambda x: x[1], reverse=True)[:top_n]
    dpts_items = sorted(dpts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    print(f"{'Src IP':<25} {'Src Port':<15} | {'Dst IP':<25} {'Dst Port':<15}")
    print("-" * 80)
    for i in range(top_n):
        sip = f"{sips_items[i][0]} ({sips_items[i][1]})" if i < len(sips_items) else ""
        spt = f"{spts_items[i][0]} ({spts_items[i][1]})" if i < len(spts_items) else ""
        dip = f"{dips_items[i][0]} ({dips_items[i][1]})" if i < len(dips_items) else ""
        dpt = f"{dpts_items[i][0]} ({dpts_items[i][1]})" if i < len(dpts_items) else ""
        print(f"{sip:<25} {spt:<15} | {dip:<25} {dpt:<15}")

print_quadrants(sips, spts, dips, dpts, top_n=20)

