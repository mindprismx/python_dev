#!/usr/bin/env python3
# wlogs_simple.py — minimal, readable version

import os, sys, json, gzip

# ---- simple config ----
ROOT = "/home/dave/logs"  # default root
GLOB_SUFFIX = ""  # set to ".json" to only include *.json, leave "" for all
CASEFOLD = False  # lower-case string values before counting
# -----------------------

USAGE = """\
Usage:
  wlogs_simple.py [member] [top]
  wlogs_simple.py -h           # list discovered JSON member paths (quick & dirty)

Examples:
  wlogs_simple.py
  wlogs_simple.py ip 20
  wlogs_simple.py request.client_ip 50
  wlogs_simple.py -h
"""


def print_usage_and_exit(code=0):
    sys.stdout.write(USAGE)
    sys.exit(code)


def effective_root():
    # if we are already under /home/dave/logs, use CWD; else use ROOT
    cwd = os.getcwd()
    return cwd if cwd.startswith(ROOT) else ROOT


def iter_files_basic(root):
    # super basic os.walk; no pathlib, no type hints, no fancy filters
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if GLOB_SUFFIX and not name.endswith(GLOB_SUFFIX):
                continue
            yield os.path.join(dirpath, name)


def open_maybe_gzip(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def json_objects_from_file_basic(path):
    # very naive: assumes one JSON object per line (common for logs).
    # If a line doesn't parse, we skip it.
    try:
        with open_maybe_gzip(path) as fh:
            for line in fh:
                s = line.strip()
                if not s or (s[0] not in "{["):
                    continue
                try:
                    yield json.loads(s)
                except Exception:
                    # ignore bad lines; this is the "brittle is fine" version
                    pass
    except Exception:
        # unreadable file? skip
        return


def get_dotted_basic(obj, dotted):
    # ultra-simple dot traversal: dicts only; no list indices
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def coerce_value_basic(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        return val.casefold() if CASEFOLD else val
    # fallback: stringify
    try:
        return json.dumps(val, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(val)


def list_members_quick(root):
    # quick & dirty: recursively walk dicts and yield dot paths (ignores lists)
    seen = set()

    def walk(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                path = f"{prefix}.{k}" if prefix else k
                if path not in seen:
                    seen.add(path)
                walk(v, path)
        # if it's a list, we don't descend (keeping it simple)

    for path in iter_files_basic(root):
        for obj in json_objects_from_file_basic(path):
            walk(obj)

    for p in sorted(seen):
        print(p)


def parse_args(argv):
    if len(argv) >= 2 and argv[1] == "-h":
        return ("__LIST__", 10)
    member = "ip"
    top = 10
    if len(argv) >= 2 and argv[1]:
        member = argv[1]
    if len(argv) >= 3 and argv[2]:
        try:
            top = int(argv[2])
        except Exception:
            top = 10
    return (member, top)


def main():
    if len(sys.argv) == 1:
        # no args is fine
        pass
    elif sys.argv[1] in ("-?", "--help"):
        print_usage_and_exit(0)

    member, top = parse_args(sys.argv)
    root = effective_root()

    if member == "__LIST__":
        list_members_quick(root)
        return

    # manual counter using a dict
    counts = {}
    files_scanned = 0
    objs_seen = 0

    for path in iter_files_basic(root):
        files_scanned += 1
        for obj in json_objects_from_file_basic(path):
            objs_seen += 1
            val = get_dotted_basic(obj, member)
            if val is None:
                continue
            key = coerce_value_basic(val)
            if key is None:
                continue
            counts[key] = counts.get(key, 0) + 1

    if not counts:
        print("(no values found for member '%s' under %s)" % (member, root))
        return

    # sort by count desc, then by key asc (basic, deterministic)
    items = sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))

    # print top N in a simple aligned table (values left, counts right)
    top_items = items[:top]
    left_width = max(len(str(k)) for k, _ in top_items)
    right_width = max(len(str(v)) for _, v in top_items)
    for k, v in top_items:
        print(str(k).ljust(left_width), str(v).rjust(right_width))


if __name__ == "__main__":
    main()
