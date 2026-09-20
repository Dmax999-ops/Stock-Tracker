#!/usr/bin/env python3
"""
Push an alert ONLY when a holding changes state.

Silence is the design. A daily notification that nothing happened is how you learn
to ignore the one that matters.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

PRIORITY = {"BUY": "high", "REDUCE": "high", "WATCH": "default", "HOLD": "low"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--signals", required=True)
    a = ap.parse_args()

    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        print("NTFY_TOPIC not set — no alert sent.")
        return 0

    payload = json.loads(Path(a.signals).read_text())
    changed = [h for h in payload["holdings"] if h.get("changed_today")]
    if not changed:
        print("No state changes — staying quiet.")
        return 0

    actionable = [h for h in changed if h["action"] in ("BUY", "REDUCE")]
    if not actionable:
        print(f"{len(changed)} state change(s), none actionable — staying quiet.")
        return 0

    lines = [f"{h['ticker']}: {h['previous_state']} -> {h['state']} = {h['action']}"
             for h in actionable]
    body = "\n".join(lines)
    prio = "high" if any(h["action"] in ("BUY", "REDUCE") for h in actionable) else "default"

    r = requests.post(f"https://ntfy.sh/{topic}", data=body.encode(),
                      headers={"Title": f"{len(actionable)} signal change(s)",
                               "Priority": prio, "Tags": "chart_with_upwards_trend"},
                      timeout=20)
    print(f"alert sent ({r.status_code}):\n{body}")
    return 0 if r.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
