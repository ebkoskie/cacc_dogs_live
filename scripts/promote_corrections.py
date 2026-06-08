"""Promote ephemeral pavilion corrections into durable, version-controlled files.

Admin corrections are made on the shelter floor and land in the serverless
worker's KV (transient). This job — run by a dedicated low-frequency workflow —
pulls the worker's pending corrections and lifts the *durable* parts into git:

  - data/aliases.json        learned "as-read -> correct name" mappings the
                             build consults before fuzzy matching (self-healing
                             of recurring misreads)
  - data/corrections_log.jsonl   append-only audit trail / future eval set

Stdlib only. Degrades to a no-op when the endpoint is unset or unreachable, so
the workflow never fails the repo because the worker is down.
"""

import http.client
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ALIASES_PATH = Path("data/aliases.json")
LOG_PATH = Path("data/corrections_log.jsonl")
TIMEOUT = 15

# Defense in depth: the worker is expected to validate/clamp, but this is the
# last hop before values land in git history, so clamp here too.
MAX_ALIAS_LEN = 80
MAX_LOG_FIELD_LEN = 200
MAX_LOG_ENTRY_BYTES = 2000
MAX_NEW_PER_RUN = 2000
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")


def _clean(value, maxlen):
    """Strip control characters and clamp length."""
    return _CTRL_RE.sub("", str(value)).strip()[:maxlen]


def _endpoint():
    base = os.environ.get("PAVILION_API_BASE", "").rstrip("/")
    return f"{base}/export-corrections" if base else ""


def _fetch_pending(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    token = os.environ.get("PAVILION_ADMIN_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.load(resp)
    return data if isinstance(data, dict) else {}


def _load_aliases():
    try:
        data = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _existing_log_ids():
    # Stream line-by-line so the audit log doesn't have to be loaded whole as it
    # grows over the years.
    ids = set()
    if not LOG_PATH.exists():
        return ids
    try:
        with LOG_PATH.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict) and entry.get("id"):
                    ids.add(entry["id"])
    except OSError:
        pass
    return ids


def main():
    url = _endpoint()
    if not url:
        print("PAVILION_API_BASE not set; nothing to promote.")
        return 0
    try:
        pending = _fetch_pending(url)
    except (
        urllib.error.URLError,
        http.client.HTTPException,
        TimeoutError,
        ValueError,
        OSError,
    ) as e:
        print(f"Could not fetch corrections ({e}); skipping.")
        return 0

    ALIASES_PATH.parent.mkdir(parents=True, exist_ok=True)

    # --- Merge learned aliases (normalized key -> correct name) ---
    aliases = _load_aliases()
    new_aliases = 0
    for raw_key, value in (pending.get("aliases") or {}).items():
        key = " ".join(_clean(raw_key, MAX_ALIAS_LEN).lower().split())
        clean_value = _clean(value, MAX_ALIAS_LEN)
        if key and clean_value and aliases.get(key) != clean_value:
            aliases[key] = clean_value
            new_aliases += 1
            if new_aliases >= MAX_NEW_PER_RUN:
                break
    if new_aliases:
        # Atomic write: a killed runner or full disk must not truncate aliases.json.
        tmp_fd, tmp_path = tempfile.mkstemp(dir=ALIASES_PATH.parent, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(
                    dict(sorted(aliases.items())), f, indent=2, ensure_ascii=False
                )
                f.write("\n")
            os.replace(tmp_path, ALIASES_PATH)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    # --- Append new audit-log entries (deduped by id) ---
    seen = _existing_log_ids()
    appended = 0
    with LOG_PATH.open("a", encoding="utf-8") as f:
        for entry in pending.get("log") or []:
            if appended >= MAX_NEW_PER_RUN:
                break
            if not isinstance(entry, dict):
                continue
            # Clamp every string field, then bound the whole entry's size.
            clamped = {
                k: (_clean(v, MAX_LOG_FIELD_LEN) if isinstance(v, str) else v)
                for k, v in entry.items()
            }
            eid = clamped.get("id")
            if eid and eid in seen:
                continue
            line = json.dumps(clamped, ensure_ascii=False)
            if len(line.encode("utf-8")) > MAX_LOG_ENTRY_BYTES:
                print(f"  (skipped oversized log entry id={eid})")
                continue
            f.write(line + "\n")
            if eid:
                seen.add(eid)
            appended += 1

    print(f"Promoted {new_aliases} new alias(es); appended {appended} log entr(ies).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
