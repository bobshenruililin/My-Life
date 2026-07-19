#!/usr/bin/env python3
"""Validate opportunities.json schema and date sanity."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

REQUIRED = {"id", "org", "programme", "category", "priority"}
PRIORITIES = {"committed", "critical", "high", "medium", "low"}
CONFLICTS = {"none", "possible", "likely", None}


def main() -> int:
    path = Path(__file__).resolve().parents[1] / "data" / "opportunities.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    opps = data["opportunities"]
    ids = set()
    errors = []
    warnings = []
    for o in opps:
        missing = REQUIRED - set(o)
        if missing:
            errors.append(f"{o.get('id')}: missing {missing}")
        if o.get("id") in ids:
            errors.append(f"duplicate id: {o.get('id')}")
        ids.add(o.get("id"))
        if o.get("priority") not in PRIORITIES:
            errors.append(f"{o.get('id')}: bad priority {o.get('priority')}")
        if o.get("laidlaw_conflict") not in CONFLICTS:
            errors.append(f"{o.get('id')}: bad laidlaw_conflict")
        for field in ("app_open", "app_close", "placement_start", "placement_end"):
            val = o.get(field)
            if val:
                try:
                    date.fromisoformat(val)
                except ValueError:
                    errors.append(f"{o.get('id')}: bad date {field}={val}")
        open_, close = o.get("app_open"), o.get("app_close")
        if open_ and close and open_ > close:
            warnings.append(f"{o.get('id')}: app_open after app_close")
        if o.get("laidlaw_conflict") == "likely" and o.get("priority") == "critical":
            warnings.append(f"{o.get('id')}: critical but likely LiA conflict — intentional?")
    print(f"Validated {len(opps)} opportunities, {len(ids)} unique ids")
    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
