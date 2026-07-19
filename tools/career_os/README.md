# Career OS

Automates the high-value parts of the HKU Law / capital-runway strategy:

- **Summer 2027 opportunity database** (law VS, quant, regulators, research, VC) with **Laidlaw LiA conflict flags**
- Deadline listing + `.ics` calendar export
- Laidlaw-aware summer planner
- CRM + application tracker
- Cold-email renderer (partner / professor / follow-up)
- Case-object + Anki TSV export
- Monthly scorecard + weekly report

## Constraint (read this)

You already have **Laidlaw Leadership in Action** for Summer 2027 (~6 immersive weeks, Jun–Aug).  
Default assumption in `data/student_profile.json`: **2027-06-15 → 2027-07-26** — **replace with exact Horizons dates**.

Do **not** double-book overlapping full-time internships without written approval.

**Prefer instead:** Dec 2026–Feb 2027 quant (Jane Street / Jump / Flow Traders), winter law schemes (Cleary, Reed Smith), SFC winter, Jan–Jun HKMA placements, AIIFL/LITE research, Betatron part-time.

## Setup

```bash
cd tools/career_os
pip install -r requirements.txt
chmod +x career-os
```

## Commands

```bash
# Deadlines (next 60 days)
./career-os deadlines --within-days 60 --urls

# Laidlaw-safe only
./career-os deadlines --laidlaw-safe --include-rolling --urls

# Full summer plan + markdown
./career-os summer-plan --urls

# Calendar for Google/Apple Calendar
./career-os ics

# Weekly action report
./career-os report

# Opportunities table
./career-os table
./career-os table --laidlaw-safe

# Emails
./career-os email --kind partner --surname "Chan" --matter "HK biotech IPO" \
  --question "cross-border clinical data in diligence" \
  --proof "prototyped an LLM healthcare tool as an MIT HK Node Youth Fellow" \
  --name "Shen Ruililin"

./career-os email --kind professor --surname "Arner" \
  --paper "digital finance / RegTech" --paraphrase "..." --hours 6

# CRM
./career-os crm-list
./career-os crm-add --name "Jane Associate" --org "Freshfields" --role-bucket associate \
  --practice "life sciences" --next-action "send artifact"

# Track applications
./career-os app-track --id janestreet-hk-winter-2026 --status prep
./career-os app-track --list

# Case objects + Anki
./career-os case-new --citation "Hong Kong Fir Shipping [1962] 2 QB 26"
./career-os anki-export --source templates/sample_anki_cards.md

# Scorecard
./career-os score-log --timed-answers 4 --retrieval-sessions 20 --conversations 2
```

## Data

| File | Purpose |
|---|---|
| `data/opportunities.json` | Curated placements (as of 2026-07-19) — verify dates on official pages |
| `data/student_profile.json` | LiA dates, wedge, proofs |
| `state/crm.csv` | Seeded faculty targets |
| `state/applications.csv` | Application status |
| `state/quant_sprint.csv` | 12-week quant falsification log |
| `state/scorecard.csv` | Monthly metrics |

## Verify before applying

Dates marked from prior-cycle patterns are **expected**, not guarantees. Always confirm on the firm’s careers page. Eligibility depends on **years until graduation** after transfer credit mapping — not “Year 1” vanity labels.
