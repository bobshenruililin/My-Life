# My-Life
Using AI to optimize my life.

## Strategic audits

- [`strategic-audits/hku-govt-laws-llb-capital-runway-audit.md`](strategic-audits/hku-govt-laws-llb-capital-runway-audit.md) — Ultra-deep career/capital strategy for HKU BSocSc(Govt&Laws)&LLB transfer (triangulated vs GPT sample, Jul 2026)
- [`strategic-audits/implementation-kit.md`](strategic-audits/implementation-kit.md) — Copy-paste emails, CRM, Anki recipes, scorecards, sprint logs
- [`strategic-audits/truth-audit-cheat-sheet.md`](strategic-audits/truth-audit-cheat-sheet.md) — One-page GPT vs reality matrix
- [`strategic-audits/summer-2027-laidlaw-plan.md`](strategic-audits/summer-2027-laidlaw-plan.md) — Summer 2027 plan with **Laidlaw LiA** conflict handling
- [`strategic-audits/placements-summer-2027.md`](strategic-audits/placements-summer-2027.md) — Full placement table (58 curated opportunities)
- [`strategic-audits/placements-laidlaw-compatible.md`](strategic-audits/placements-laidlaw-compatible.md) — LiA-safe subset

## Career OS (automation)

Python toolkit under [`tools/career_os/`](tools/career_os/):

```bash
cd tools/career_os && pip install -r requirements.txt && make all
./career-os deadlines --within-days 60 --urls
./career-os summer-plan --urls
./career-os ics   # import state/deadlines.ics into Google Calendar
```

Features: deadline ICS, Laidlaw-aware summer planner, CRM, application tracker, email renderer, Anki export, case objects, weekly GitHub Action report.
