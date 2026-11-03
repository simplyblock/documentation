"""JSON-lines event log shared by the API, the MCP endpoint, and pre-answering."""

from __future__ import annotations

import json
import sys
import time

from .config import settings


def log(event: str, **fields) -> None:
    line = json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, **fields})
    if settings.log_file:
        with open(settings.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    else:
        print(line, file=sys.stdout, flush=True)
