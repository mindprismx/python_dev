#!/usr/bin/env python3
"""
wlogs.py — count most frequent values for a given JSON field across log files.

Usage:
  wlogs.py [-h] [-v] [member] [top]

Options:
  -h      Scan logs and print all JSON member paths discovered (dot paths), then exit
  -v      Verbose: print the summary line at the end of a normal run

Args:
  member  JSON field (dot.notation allowed). Default: ip
  top     Number of top results to print. Default: 10

Examples:
  wlogs.py
  wlogs.py ip 20
  wlogs.py -v request.client_ip 50
  wlogs.py -h
"""

from __future__ import annotations
import gzip
import io
import json
import os
import sys
import subprocess
from pathlib import Path
from collections import Counter
from typing import Any, Iterator, Union, Optional
from datetime import datetime, timezone


# -------- config-like defaults (no flags) --------
def default_root() -> Path:
    cwd = Path.cwd()
    return cwd if str(cwd).startswith("/home/dave/logs") else Path("/home/dave/logs")


ROOT: Path = default_root()
GLOB: str = "*"  # filenames to include
CASEFOLD: bool = False  # case-fold string values before counting
# -------------------------------------------------


def usage() -> None:
    print(__doc__.strip())


def parse_args(argv: list[str]) -> tuple[str, int, bool, bool]:
    """
    Returns: (member, top, list_members_flag, verbose_flag)
    """
    member = "ip"
    top = 10
    list_members_flag = False
    verbose_flag = False
    positional: list[str] = []

    for a in argv[1:]:
        if a == "-h":
            list_members_flag = True
        elif a == "-v":
            verbose_flag = True
        elif a.startswith("-"):
            print(f"unknown option: {a}", file=sys.stderr)
            usage()
            sys.exit(2)
        else:
            positional.append(a)

    if len(positional) >= 1 and positional[0]:
        member = positional[0]
    if len(positional) >= 2 and positional[1]:
        try:
            top = int(positional[1])
        except ValueError:
            print(f"invalid top '{positional[1]}', using default 10", file=sys.stderr)
            top = 10

    return member, top, list_members_flag, verbose_flag


def iter_files(root: Path, pattern: str) -> Iterator[Path]:
    for dirpath, _, filenames in os.walk(root):
        d = Path(dirpath)
        for name in filenames:
            if Path(name).match(pattern):
                yield d / name


def open_maybe_gzip(p: Path) -> io.TextIOBase:
    if p.suffix == ".gz":
        return io.TextIOWrapper(gzip.open(p, "rb"), encoding="utf-8", errors="replace")
    return open(p, "r", encoding="utf-8", errors="replace")


def json_objects_from_file(p: Path) -> Iterator[Any]:
    tried_full = False
    with open_maybe_gzip(p) as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            if not (s.startswith("{") or s.startswith("[")):
                continue
            try:
                obj = json.loads(s)
                yield obj
            except json.JSONDecodeError:
                tried_full = True
                break

    if tried_full:
        with open_maybe_gzip(p) as fh2:
            try:
                doc = json.load(fh2)
            except json.JSONDecodeError:
                return
        if isinstance(doc, list):
            for item in doc:
                yield item
        else:
            yield doc


def get_dotted(obj: Any, path: str) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part, None)
        elif isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError:
                return None
            if idx < 0 or idx >= len(cur):
                return None
            cur = cur[idx]
        else:
            return None
    return cur


def coerce_value(val: Any, casefold: bool) -> Union[str, int, float, None]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, (str, bytes)):
        s = val.decode("utf-8", "replace") if isinstance(val, bytes) else val
        return s.casefold() if casefold else s
    try:
        return json.dumps(val, sort_keys=True, ensure_ascii=False)
    except Exception:
        return str(val)


def _parse_iso8601(s: str) -> Optional[datetime]:
    try:
        if s.endswith("Z"):
            return datetime.fromisoformat(s[:-1] + "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _parse_epoch(num: Union[int, float]) -> Optional[datetime]:
    try:
        if num > 10_000_000_000:
            dt = datetime.fromtimestamp(num / 1000, tz=timezone.utc)
        else:
            dt = datetime.fromtimestamp(num, tz=timezone.utc)
    except Exception:
        return None
    if (
        datetime(2000, 1, 1, tzinfo=timezone.utc)
        <= dt
        <= datetime(2100, 1, 1, tzinfo=timezone.utc)
    ):
        return dt
    return None


def iter_timestamps(obj: Any) -> Iterator[datetime]:
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, (int, float)):
            dt = _parse_epoch(cur)
            if dt:
                yield dt
        elif isinstance(cur, (str, bytes)):
            s = cur.decode("utf-8", "replace") if isinstance(cur, bytes) else cur
            dt = _parse_iso8601(s)
            if dt:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                yield dt


def fmt_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "n/a"
    return dt.astimezone(timezone.utc).strftime("%m-%d-%y %H:%M:%S")


def normalize_asn(value: Union[str, int]) -> Optional[str]:
    if isinstance(value, int):
        return str(value)
    s = str(value).strip()
    if not s:
        return None
    if s.lower().startswith("as"):
        s = s[2:]
    s = "".join(ch for ch in s if ch.isdigit())
    return s or None


def cymru_asn_name(asn_numeric: str) -> str:
    try:
        cmd = (
            f"whois -h whois.cymru.com ' -v AS{asn_numeric}' "
            "| awk -F'|' 'NR==2 {gsub(/^ +| +$/,\"\",$5); print $5}'"
        )
        org = subprocess.check_output(cmd, shell=True, text=True).strip()
        return org or "Unknown"
    except Exception:
        return "Unknown"


def print_table(member: str, counter: Counter, top: int) -> None:
    items = counter.most_common(top)
    if not items:
        return

    if member in ("asn", "ua"):
        # counts left, values right
        max_count_width = max(len(str(v)) for _, v in items)
        for raw_val, cnt in items:
            val = raw_val
            if member == "asn":
                asn_str = normalize_asn(raw_val)
                if asn_str:
                    org = cymru_asn_name(asn_str)
                    val = f"{org} (AS{asn_str})"
            print(f"{str(cnt).rjust(max_count_width)}   {val}")
    else:
        # values left, counts right
        max_val_width = max(len(str(k)) for k, _ in items)
        max_count_width = max(len(str(v)) for _, v in items)
        for k, v in items:
            print(f"{str(k).ljust(max_val_width)}   {str(v).rjust(max_count_width)}")


# -------- -h support: enumerate JSON member paths --------
def iter_member_paths(obj: Any, prefix: str = "") -> Iterator[str]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            yield path
            yield from iter_member_paths(v, path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            path = f"{prefix}.{i}" if prefix else str(i)
            yield path
            yield from iter_member_paths(v, path)


def list_members(root: Path) -> None:
    seen: set[str] = set()
    for p in iter_files(root, GLOB):
        for obj in json_objects_from_file(p):
            for path in iter_member_paths(obj):
                seen.add(path)
    for path in sorted(seen):
        print(path)


# ---------------------------------------------------------


def main() -> None:
    member, top, list_flag, verbose = parse_args(sys.argv)

    if list_flag:
        # -h: list discovered JSON member paths and exit
        list_members(ROOT)
        return

    counter: Counter = Counter()
    files_scanned = 0
    objs_seen = 0
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None

    for p in iter_files(ROOT, GLOB):
        files_scanned += 1
        for obj in json_objects_from_file(p):
            objs_seen += 1
            for ts in iter_timestamps(obj):
                if earliest is None or ts < earliest:
                    earliest = ts
                if latest is None or ts > latest:
                    latest = ts
            val = get_dotted(obj, member)
            if val is None:
                continue
            key = coerce_value(val, CASEFOLD)
            if key is None:
                continue
            counter[key] += 1

    if not counter:
        print(f"(no values found for member '{member}' under {ROOT})")
        if verbose:
            print(
                f"# files={files_scanned} objects={objs_seen} unique=0 "
                f"earliest={fmt_dt(earliest)} latest={fmt_dt(latest)}",
                file=sys.stderr,
            )
        return

    print_table(member, counter, top)

    if verbose:
        print(
            f"# files={files_scanned} objects={objs_seen} unique={len(counter)} "
            f"earliest={fmt_dt(earliest)} latest={fmt_dt(latest)}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
