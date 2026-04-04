#!/usr/bin/env python3
"""
pagecrawl.py

Usage:
  pagecrawl.py /path/to/urls.txt
Optional env vars:
  PAGECRAWL_HOME  - base dir to store data (default: ~/.pagecrawl)
  SMTP_SERVER     - smtp hostname (if not set, tries local sendmail)
  SMTP_PORT       - smtp port (default 587)
  SMTP_USER       - smtp auth user (optional)
  SMTP_PASS       - smtp auth password (optional)
  FROM_ADDR       - envelope From header (default: pagecrawl@`hostname`)
Behavior:
  - first non-comment line in urls file must be an email address (destination)
  - subsequent non-comment lines are URL entries; optionally "label|url"
  - lines beginning with '#' are comments and ignored
"""
from __future__ import annotations
import os
import sys
import re
import hashlib
import json
import time
import html
import datetime
import subprocess
import smtplib
import shutil
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Tuple, Optional, List
from urllib.parse import urlparse
import difflib

# requests is nicer; fallback to urllib if not present
try:
    import requests
except Exception:
    requests = None
    import urllib.request as _urllib
    from urllib.error import URLError, HTTPError

# ---------- Config ----------
DEFAULT_HOME = os.environ.get("PAGECRAWL_HOME", os.path.expanduser("~/.pagecrawl"))
USER_AGENT = "pagecrawl/1.0 (+https://augros.org)"
REQUEST_TIMEOUT = 30  # seconds
MAX_INLINE_DIFF_CHARS = 20000
MAX_INLINE_DIFF_LINES = 1200
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
# ----------------------------

def ensure_dir(path: str, mode: int = 0o700) -> None:
    os.makedirs(path, exist_ok=True)
    try:
        os.chmod(path, mode)
    except Exception:
        pass

def slug_for_url(url: str) -> str:
    # deterministic short slug: host + short hash of url
    p = urlparse(url)
    host = p.netloc.replace(":", "_")
    h = hashlib.sha1(url.encode("utf8")).hexdigest()[:10]
    # use path parts but avoid crazy chars
    path_part = re.sub(r'[^A-Za-z0-9\-_]+', '_', (p.path or "").strip("/"))[:40] or "root"
    return f"{host}__{path_part}__{h}"

def fetch_url(url: str) -> Tuple[bool, Optional[str], Optional[bytes], str]:
    """Return (ok_text, text, binary, reason)
       - if text page, text is str, binary is None
       - if binary, text is None, binary is bytes and reason describes content/type
       - on error, ok_text False and reason contains error
    """
    headers = {"User-Agent": USER_AGENT}
    if requests:
        try:
            r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            r.raise_for_status()
            ctype = (r.headers.get("Content-Type") or "").split(";")[0].lower()
            if ctype.startswith("text") or ctype in ("application/json", "application/xml", "application/xhtml+xml"):
                # requests will decode according to headers
                return True, r.text, None, ctype or "text"
            else:
                return True, None, r.content, ctype or "binary"
        except Exception as e:
            return False, None, None, f"fetch-error: {e}"
    else:
        # urllib fallback
        try:
            req = _urllib.Request(url, headers=headers)
            with _urllib.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = resp.read()
                ctype = (resp.headers.get("Content-Type") or "").split(";")[0].lower()
                if ctype.startswith("text") or ctype in ("application/json", "application/xml", "application/xhtml+xml"):
                    # try decode using charset in header
                    charset = "utf-8"
                    m = re.search(r"charset=([^;]+)", (resp.headers.get("Content-Type") or ""), re.I)
                    if m:
                        charset = m.group(1).strip()
                    try:
                        text = raw.decode(charset, errors="replace")
                    except Exception:
                        text = raw.decode("utf-8", errors="replace")
                    return True, text, None, ctype or "text"
                else:
                    return True, None, raw, ctype or "binary"
        except HTTPError as he:
            return False, None, None, f"HTTPError {he.code}"
        except URLError as ue:
            return False, None, None, f"URLError {ue}"
        except Exception as e:
            return False, None, None, f"fetch-error: {e}"

def timestamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def write_snapshot(base_dir: str, slug: str, content: bytes, is_text: bool) -> str:
    d = os.path.join(base_dir, "data", slug)
    history = os.path.join(d, "history")
    ensure_dir(history)
    fname = f"{timestamp()}.txt" if is_text else f"{timestamp()}.bin"
    path = os.path.join(history, fname)
    with open(path, "wb") as fh:
        fh.write(content)
    # update latest symlink / file
    latest = os.path.join(d, "latest")
    try:
        if os.path.islink(latest) or os.path.exists(latest):
            try:
                os.remove(latest)
            except Exception:
                pass
        os.symlink(os.path.relpath(path, d), latest)
    except Exception:
        # fallback: copy
        try:
            shutil.copy2(path, latest)
        except Exception:
            pass
    return path

def read_latest(base_dir: str, slug: str) -> Optional[bytes]:
    latest = os.path.join(base_dir, "data", slug, "latest")
    if not os.path.exists(latest):
        return None
    try:
        with open(latest, "rb") as fh:
            return fh.read()
    except Exception:
        return None

def send_email_via_smtp(msg: EmailMessage) -> Tuple[bool, str]:
    smtp_server = os.environ.get("SMTP_SERVER")
    if not smtp_server:
        return False, "no SMTP_SERVER configured"
    port = int(os.environ.get("SMTP_PORT", SMTP_PORT))
    user = os.environ.get("SMTP_USER")
    pwd = os.environ.get("SMTP_PASS")
    try:
        # prefer TLS (STARTTLS)
        s = smtplib.SMTP(smtp_server, port, timeout=30)
        s.ehlo()
        try:
            s.starttls()
            s.ehlo()
        except Exception:
            pass
        if user and pwd:
            s.login(user, pwd)
        s.send_message(msg)
        s.quit()
        return True, f"sent via {smtp_server}:{port}"
    except Exception as e:
        return False, f"smtp-send-failed: {e}"

def send_email_via_sendmail(msg: EmailMessage) -> Tuple[bool, str]:
    """
    Prefer msmtp if present. Use MSMTP_ACCOUNT env var to select account (e.g. 'oci').
    Falls back to a system sendmail if msmtp isn't installed.
    """
    msmtp_path = shutil.which("msmtp")
    if msmtp_path:
        account = os.environ.get("MSMTP_ACCOUNT")
        cmd = [msmtp_path]
        if account:
            cmd += ["--account", account]
        # -t reads recipients from headers; -i ignore single dot lines
        cmd += ["-t", "-i"]
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            p.communicate(input=msg.as_bytes())
            rc = p.returncode or 0
            if rc == 0:
                return True, f"sent via msmtp ({' '.join(cmd)})"
            else:
                return False, f"msmtp exit {rc}"
        except Exception as e:
            return False, f"msmtp-failed: {e}"

    # fallback: look for sendmail binary
    sendmail = shutil.which("sendmail") or shutil.which("/usr/sbin/sendmail")
    if not sendmail:
        return False, "sendmail/msmtp not found"
    try:
        p = subprocess.Popen([sendmail, "-t", "-i"], stdin=subprocess.PIPE)
        p.communicate(input=msg.as_bytes())
        rc = p.returncode or 0
        if rc == 0:
            return True, f"sent via sendmail({sendmail})"
        else:
            return False, f"sendmail exit {rc}"
    except Exception as e:
        return False, f"sendmail-failed: {e}"


def send_report(to_addr: str, subject: str, plain_body: str, attachments: List[Tuple[str, bytes, str]], from_addr: Optional[str] = None) -> Tuple[bool, str]:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=False)
    msg["To"] = to_addr
    host = os.uname().nodename if hasattr(os, "uname") else "pagecrawl"
    msg["From"] = from_addr or os.environ.get("FROM_ADDR") or f"pagecrawl@{host}"

    # Plain text fallback (keep as-is)
    msg.set_content(plain_body)

    # HTML alternative: monospace <pre> with sensible fallbacks.
    # Consolas / Roboto Mono are preferred, then Courier New, then generic monospace.
    escaped = html.escape(plain_body)
    html_body = f"""\
    <html>
      <body>
        <div style="font-family: Consolas, 'Roboto Mono', 'Courier New', monospace; font-size: 12px; line-height:1.3; white-space: pre-wrap;">
{escaped}
        </div>
      </body>
    </html>
    """
    msg.add_alternative(html_body, subtype="html")

    # Attach any diff files (keep behaviour you already have)
    for filename, data, mimetype in attachments:
        maintype, subtype = mimetype.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    # try SMTP first
    ok, reason = send_email_via_smtp(msg)
    if ok:
        return True, reason
    # fallback to sendmail/msmtp wrapper
    ok2, reason2 = send_email_via_sendmail(msg)
    if ok2:
        return True, reason2
    return False, f"smtp: {reason}; sendmail: {reason2}"


def parse_urls_file(path: str) -> Tuple[str, List[Tuple[str,str]]]:
    """Return (mailto, list of (label,url))"""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    to_addr = None
    items = []
    with open(path, "r", encoding="utf8") as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if to_addr is None:
                # expect an email address
                if s.lower().startswith("mailto:"):
                    s2 = s.split(":",1)[1].strip()
                else:
                    s2 = s
                if not re.match(r"[^@ \t]+@[^@ \t]+\.[^@ \t]+", s2):
                    raise ValueError(f"expected email on first non-comment line, got: {s}")
                to_addr = s2
                continue
            # parse optional label|url
            if "|" in s:
                label, url = s.split("|", 1)
                label = label.strip()
                url = url.strip()
            else:
                label = ""
                url = s
            items.append((label or url, url))
    if to_addr is None:
        raise ValueError("no destination email found in urls file (first non-comment line must be an email)")
    return to_addr, items

def make_diff_text(old: str, new: str, old_name: str, new_name: str) -> str:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=old_name, tofile=new_name, lineterm="")
    return "\n".join(diff)

def main(argv):
    if len(argv) < 2:
        print("usage: pagecrawl.py /path/to/urls.txt", file=sys.stderr)
        return 2
    urls_file = argv[1]
    base = os.environ.get("PAGECRAWL_HOME", DEFAULT_HOME)
    ensure_dir(base)
    ensure_dir(os.path.join(base, "data"))
    ensure_dir(os.path.join(base, "reports"))
    try:
        to_addr, entries = parse_urls_file(urls_file)
    except Exception as e:
        print(f"failed to parse urls file: {e}", file=sys.stderr)
        return 3

    summary = []
    attachments = []
    now = timestamp()
    changed_any = False
    for label, url in entries:
        slug = slug_for_url(url)
        safe_label = re.sub(r"[^\w\-_\. ]", "_", label)[:60]
        result = {"label": label, "url": url, "status": None, "reason": None, "diff_short": None, "full_diff_path": None}
        ok, text, binary, reason = fetch_url(url)
        result["status"] = "error" if not ok else "fetched"
        result["reason"] = reason
        if not ok:
            summary.append(result)
            continue
        ddir = os.path.join(base, "data", slug)
        ensure_dir(ddir)
        latest = read_latest(base, slug)
        is_text = text is not None
        if is_text:
            content = text.encode("utf8")
        else:
            content = binary
        # write snapshot (history + latest)
        saved = write_snapshot(base, slug, content, is_text)
        result["saved"] = saved
        if latest is None:
            result["status"] = "new"
            summary.append(result)
            continue
        # compare
        if is_text:
            try:
                old_text = latest.decode("utf8", errors="replace")
            except Exception:
                old_text = latest.decode("latin1", errors="replace")
            new_text = text
            diff_text = make_diff_text(old_text, new_text, "previous", "current")
            if diff_text.strip():
                changed_any = True
                result["status"] = "changed"
                # truncate if too big for inline
                if len(diff_text) > MAX_INLINE_DIFF_CHARS or diff_text.count("\n") > MAX_INLINE_DIFF_LINES:
                    # save full diff to reports dir and attach
                    diff_fname = f"{now}__{slug}.diff"
                    diff_path = os.path.join(base, "reports", diff_fname)
                    with open(diff_path, "w", encoding="utf8") as fh:
                        fh.write(diff_text)
                    result["full_diff_path"] = diff_path
                    short = "\n".join(diff_text.splitlines()[:MAX_INLINE_DIFF_LINES])
                    short = short + f"\n\n[diff truncated; full diff saved at {diff_path}]\n"
                    result["diff_short"] = short
                    # attach full diff
                    try:
                        with open(diff_path, "rb") as fh:
                            attachments.append((diff_fname, fh.read(), "text/plain"))
                    except Exception:
                        pass
                else:
                    result["diff_short"] = diff_text
            else:
                result["status"] = "unchanged"
        else:
            # binary: compare sha256
            old_hash = hashlib.sha256(latest).hexdigest()
            new_hash = hashlib.sha256(content).hexdigest()
            if old_hash != new_hash:
                changed_any = True
                result["status"] = "changed-binary"
                info = f"binary changed: old-sha256={old_hash} new-sha256={new_hash}"
                result["reason"] = info
            else:
                result["status"] = "unchanged"
        summary.append(result)

    # build email body
    lines = []
    lines.append(f"Pagecrawl report generated: {datetime.datetime.utcnow().isoformat()} UTC")
    lines.append("")
    changed_list = [r for r in summary if r.get("status", "").startswith("changed") or r.get("status") == "new" or r.get("status") == "error"]
    if not changed_list:
        lines.append("No changes detected.")
    else:
        lines.append(f"{len(changed_list)} items changed/new/error:")
        lines.append("")
        for r in changed_list:
            lines.append(f"- {r['label']}")
            lines.append(f"  URL: {r['url']}")
            lines.append(f"  status: {r['status']}")
            if r.get("reason"):
                lines.append(f"  note: {r['reason']}")
            if r.get("saved"):
                lines.append(f"  snapshot: {r['saved']}")
            if r.get("full_diff_path"):
                lines.append(f"  full diff: {r['full_diff_path']}")
            lines.append("")
            if r.get("diff_short"):
                lines.append("  --- diff (truncated) ---")
                # indent diff for readability
                for dl in r["diff_short"].splitlines():
                    lines.append("   " + dl)
                lines.append("  --- end diff ---")
                lines.append("")
    lines.append("")
    lines.append("Complete per-URL statuses:")
    for r in summary:
        lines.append(f"- {r['label']}: {r['status']}")
    body = "\n".join(lines)
    subject = f"pagecrawl report: {('changes' if changed_any else 'no-changes')} ({len(changed_list)} items)"

    force_send = os.environ.get("FORCE_SEND_ON_NOCHANGE", "0").lower() in ("1", "true", "yes")
    heartbeat_daily = os.environ.get("HEARTBEAT_DAILY", "0").lower() in ("1", "true", "yes")
    heartbeat_file = os.path.join(base, "last_heartbeat.txt")

    send_now = changed_any or force_send

    if not send_now and heartbeat_daily:
        try:
            if os.path.exists(heartbeat_file):
                # last heartbeat epoch stored
                with open(heartbeat_file, "r") as fh:
                    last = float(fh.read().strip() or "0")
            else:
                last = 0.0
            now_epoch = time.time()
            if now_epoch - last >= 24 * 3600:
                send_now = True
                with open(heartbeat_file, "w") as fh:
                    fh.write(str(now_epoch))
        except Exception:
            # if any error, do not block notifications on real changes
            send_now = changed_any or force_send

    if not send_now:
        # no changes and not forced: log and exit quietly
        # append a short line to last_run log for audit
        try:
            with open(os.path.join(base, "last_run.log"), "a") as fh:
                fh.write(f"{timestamp()} - no changes detected\n")
        except Exception:
            pass
        # print("no changes detected; skipping email")
        return 0

    # if we get here, actually send the email
    ok, reason = send_report(to_addr, subject, body, attachments)
    # out_line = f"report sent: {ok} ({reason})"
    # print(out_line)
    return 0 if ok else 4

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
