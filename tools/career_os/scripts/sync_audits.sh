#!/usr/bin/env bash
# Sync generated Career OS reports into strategic-audits/ for easy reading.
set -euo pipefail
COS="$(cd "$(dirname "$0")/.." && pwd)"
AUD="$(cd "$COS/../.." && pwd)/strategic-audits"
# COS = tools/career_os ; repo root = parent of tools
REPO="$(cd "$COS/../.." && pwd)"
AUD="$REPO/strategic-audits"
mkdir -p "$AUD"
cd "$COS"
PYTHONPATH=. python3 -m career_os report
PYTHONPATH=. python3 -m career_os summer-plan
PYTHONPATH=. python3 -m career_os table
PYTHONPATH=. python3 -m career_os table --laidlaw-safe --out state/opportunities_laidlaw_safe.md
PYTHONPATH=. python3 -m career_os ics
cp -f state/summer_2027_plan.md "$AUD/summer-2027-laidlaw-plan.md"
cp -f state/weekly_report.md "$AUD/career-os-weekly-report.md"
cp -f state/opportunities_table.md "$AUD/placements-summer-2027.md"
cp -f state/opportunities_laidlaw_safe.md "$AUD/placements-laidlaw-compatible.md"
echo "Synced reports → $AUD"
