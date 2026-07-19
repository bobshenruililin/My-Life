"""Career OS — automate HKU Law / capital-runway execution."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
STATE = ROOT / "state"
DEFAULT_OPP = DATA / "opportunities.json"
DEFAULT_CRM = STATE / "crm.csv"
DEFAULT_SCORE = STATE / "scorecard.csv"
DEFAULT_APPS = STATE / "applications.csv"
DEFAULT_PROFILE = DATA / "student_profile.json"

PRIORITY_ORDER = {"committed": 0, "critical": 1, "high": 2, "medium": 3, "low": 4}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def days_until(d: date | None, today: date | None = None) -> int | None:
    if d is None:
        return None
    today = today or date.today()
    return (d - today).days


def conflict_rank(flag: str | None) -> int:
    return {"none": 0, "possible": 1, "likely": 2}.get(flag or "", 9)


def load_opportunities(path: Path = DEFAULT_OPP) -> list[dict]:
    payload = load_json(path)
    return payload.get("opportunities", payload)


def ensure_state() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_CRM.exists():
        DEFAULT_CRM.write_text(
            "name,org,role_bucket,practice,hook_url,relevant_proof,artifact,last_contact,next_action,status,notes\n",
            encoding="utf-8",
        )
    if not DEFAULT_APPS.exists():
        DEFAULT_APPS.write_text(
            "opportunity_id,org,programme,status,applied_on,deadline,notes\n",
            encoding="utf-8",
        )
    if not DEFAULT_SCORE.exists():
        DEFAULT_SCORE.write_text(
            "month,timed_answers,retrieval_sessions,office_hours,doctrine_graphs,"
            "probability_problems,coding_exercises,simulations,transactions_analysed,"
            "conversations,followups,intros_made,artifact_shipped,runway_months,notes\n",
            encoding="utf-8",
        )


def cmd_deadlines(args: argparse.Namespace) -> int:
    opps = load_opportunities(Path(args.data))
    today = date.fromisoformat(args.today) if args.today else date.today()
    rows = []
    for o in opps:
        close = parse_date(o.get("app_close"))
        open_ = parse_date(o.get("app_open"))
        if args.laidlaw_safe and conflict_rank(o.get("laidlaw_conflict")) >= 2:
            continue
        if args.category and o.get("category") not in args.category:
            continue
        if args.priority and o.get("priority") not in args.priority:
            continue
        if close is None and open_ is None and not args.include_rolling:
            continue
        due = close or open_
        delta = days_until(due, today) if due else None
        if args.within_days is not None and (delta is None or delta > args.within_days or delta < 0):
            continue
        rows.append((PRIORITY_ORDER.get(o.get("priority", "low"), 9), delta if delta is not None else 10_000, o, due, delta))

    rows.sort(key=lambda r: (r[0], r[1], r[2].get("org", "")))
    print(f"As of {today.isoformat()} — {len(rows)} opportunities\n")
    print(f"{'PRI':8} {'DUE':12} {'DAYS':5} {'LIA':8} {'ORG':22} PROGRAMME")
    print("-" * 110)
    for _, __, o, due, delta in rows:
        due_s = due.isoformat() if due else "rolling"
        days_s = str(delta) if delta is not None else "-"
        print(
            f"{(o.get('priority') or ''):8} {due_s:12} {days_s:5} "
            f"{(o.get('laidlaw_conflict') or ''):8} {(o.get('org') or '')[:22]:22} {o.get('programme')}"
        )
        if args.urls:
            print(f"         {o.get('url')}")
    return 0


def cmd_summer_plan(args: argparse.Namespace) -> int:
    opps = load_opportunities(Path(args.data))
    profile = load_json(Path(args.profile)) if Path(args.profile).exists() else {}
    lia = profile.get("laidlaw_lia", {})
    lia_start = parse_date(lia.get("start") or "2027-06-15")
    lia_end = parse_date(lia.get("end") or "2027-07-26")

    print("SUMMER 2027 PLANNER — Laidlaw Leadership in Action locked")
    print(f"LiA assumed block: {lia_start} → {lia_end} ({(lia_end - lia_start).days // 7} weeks)")
    print("Get exact dates from HKU Horizons in writing.\n")

    buckets = {
        "compatible_now": [],
        "winter_spring_bridge": [],
        "summer_conflict_negotiate": [],
        "insight_research": [],
        "committed": [],
    }
    for o in opps:
        cat = o.get("category")
        conflict = o.get("laidlaw_conflict")
        if o.get("priority") == "committed" or cat == "committed":
            buckets["committed"].append(o)
        elif conflict == "none" and cat in {"quant", "quant_insight", "regulator", "ecosystem", "vc", "research", "insight", "law_vacation"}:
            p_start = parse_date(o.get("placement_start"))
            if p_start and p_start.year == 2026 or (p_start and p_start < lia_start):
                buckets["winter_spring_bridge"].append(o)
            elif conflict == "none":
                buckets["compatible_now"].append(o)
            else:
                buckets["compatible_now"].append(o)
        elif conflict in {"possible", "likely"} and cat in {"law_vacation", "quant", "regulator", "ecosystem"}:
            buckets["summer_conflict_negotiate"].append(o)
        elif cat in {"research", "insight", "quant_insight"}:
            buckets["insight_research"].append(o)

    # cleaner re-bucket
    compatible, bridge, conflict_list, other = [], [], [], []
    for o in opps:
        if o.get("category") == "committed" or o.get("priority") == "committed":
            continue
        flag = o.get("laidlaw_conflict")
        p_start = parse_date(o.get("placement_start"))
        p_end = parse_date(o.get("placement_end"))
        overlaps = False
        if p_start and p_end:
            overlaps = not (p_end < lia_start or p_start > lia_end)
        elif p_start and not p_end:
            overlaps = lia_start <= p_start <= lia_end
        if flag == "none" or (p_end and p_end < lia_start) or (p_start and p_start > lia_end):
            if p_end and p_end < lia_start:
                bridge.append(o)
            else:
                compatible.append(o)
        elif overlaps or flag in {"likely", "possible"}:
            conflict_list.append(o)
        else:
            other.append(o)

    def show(title: str, items: list[dict], limit: int = 25) -> None:
        print(f"\n## {title} ({len(items)})")
        items = sorted(items, key=lambda x: PRIORITY_ORDER.get(x.get("priority", "low"), 9))
        for o in items[:limit]:
            print(
                f"- [{o.get('priority')}] {o.get('org')}: {o.get('programme')}"
                f" | app_close={o.get('app_close') or 'rolling'}"
                f" | place={o.get('placement_start') or '?'}→{o.get('placement_end') or '?'}"
                f" | LIA={o.get('laidlaw_conflict')}"
            )
            if o.get("status_note"):
                print(f"  note: {o['status_note']}")
            if args.urls and o.get("url"):
                print(f"  {o['url']}")

    show("A. APPLY NOW — Laidlaw-compatible (winter / rolling / research)", bridge + [o for o in compatible if o.get("priority") in {"critical", "high"}])
    show("B. SUMMER 2027 — likely LiA conflict (apply only if dates negotiable / eligibility confirmed)", conflict_list)
    show("C. OTHER / MONITOR", other, limit=15)

    out = Path(args.out) if args.out else STATE / "summer_2027_plan.md"
    ensure_state()
    lines = [
        "# Summer 2027 Plan (auto-generated)",
        f"Generated: {date.today().isoformat()}",
        f"Laidlaw LiA assumed: {lia_start} → {lia_end}",
        "",
        "## Strategy",
        "1. Lock exact LiA dates with HKU Horizons in writing.",
        "2. Prioritise Dec 2026–Feb 2027 and winter law schemes (Cleary, Reed Smith, SFC, Jane Street, Flow Traders, Jump).",
        "3. Use Summer 2027 full-time law VS only if: (a) you are eligibility-penultimate, AND (b) firm can place you outside LiA weeks, OR (c) LiA is scheduled in a non-overlapping block.",
        "4. Do ONE deep placement + LiA — not three logos.",
        "5. Parallel: AIIFL fellowship + LITE + one depth artifact.",
        "",
    ]
    for title, items in [
        ("Laidlaw-compatible / bridge", bridge + compatible),
        ("Likely LiA conflict", conflict_list),
    ]:
        lines.append(f"## {title}")
        for o in sorted(items, key=lambda x: PRIORITY_ORDER.get(x.get("priority", "low"), 9)):
            lines.append(
                f"- **{o.get('org')}** — {o.get('programme')} "
                f"(priority={o.get('priority')}, close={o.get('app_close')}, "
                f"LIA={o.get('laidlaw_conflict')})  \n  {o.get('url')}"
            )
            if o.get("status_note"):
                lines.append(f"  - {o['status_note']}")
        lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")
    return 0


def cmd_ics(args: argparse.Namespace) -> int:
    try:
        from icalendar import Calendar, Event
    except ImportError:
        print("Install icalendar: pip install icalendar", file=sys.stderr)
        return 1

    opps = load_opportunities(Path(args.data))
    cal = Calendar()
    cal.add("prodid", "-//Career OS//HKU Law//EN")
    cal.add("version", "2.0")
    today = date.today()
    for o in opps:
        close = parse_date(o.get("app_close"))
        if not close:
            continue
        if args.laidlaw_safe and conflict_rank(o.get("laidlaw_conflict")) >= 2:
            # still include winter/non-conflict
            pass
        event = Event()
        event.add("summary", f"DEADLINE: {o.get('org')} — {o.get('programme')}")
        event.add("dtstart", close)
        event.add("dtend", close + timedelta(days=1))
        event.add(
            "description",
            f"Priority: {o.get('priority')}\n"
            f"Laidlaw conflict: {o.get('laidlaw_conflict')}\n"
            f"URL: {o.get('url')}\n"
            f"{o.get('status_note') or ''}",
        )
        event.add("uid", f"{o.get('id')}@career-os")
        cal.add_component(event)

        # reminder 14 days before if still in future
        remind = close - timedelta(days=14)
        if remind >= today:
            rem = Event()
            rem.add("summary", f"PREP (14d): {o.get('org')} application")
            rem.add("dtstart", remind)
            rem.add("dtend", remind + timedelta(days=1))
            rem.add("uid", f"{o.get('id')}-prep@career-os")
            rem.add("description", o.get("url") or "")
            cal.add_component(rem)

    ensure_state()
    out = Path(args.out) if args.out else STATE / "deadlines.ics"
    out.write_bytes(cal.to_ical())
    print(f"Wrote {out} ({len(cal.subcomponents)} events)")
    return 0


def cmd_crm_list(args: argparse.Namespace) -> int:
    ensure_state()
    path = Path(args.crm)
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("CRM empty. Add contacts with: career-os crm-add ...")
        return 0
    for r in rows:
        print(f"{r.get('status','?'):12} {r.get('name'):20} {r.get('org'):20} next={r.get('next_action')}")
    return 0


def cmd_crm_add(args: argparse.Namespace) -> int:
    ensure_state()
    path = Path(args.crm)
    fieldnames = [
        "name", "org", "role_bucket", "practice", "hook_url", "relevant_proof",
        "artifact", "last_contact", "next_action", "status", "notes",
    ]
    with path.open(newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    row = {k: getattr(args, k, "") or "" for k in fieldnames}
    row["status"] = row["status"] or "researching"
    row["last_contact"] = row["last_contact"] or ""
    existing.append(row)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(existing)
    print(f"Added {row['name']} @ {row['org']}")
    return 0


def cmd_email(args: argparse.Namespace) -> int:
    kind = args.kind
    if kind == "partner":
        path = TEMPLATES / "email_partner.md"
    elif kind == "professor":
        path = TEMPLATES / "email_professor.md"
    else:
        path = TEMPLATES / "email_followup.md"
    text = path.read_text(encoding="utf-8")
    replacements = {
        "SURNAME": args.surname or "[Surname]",
        "PROOF": args.proof or "[ONE relevant proof]",
        "MATTER": args.matter or "[specific public matter]",
        "QUESTION": args.question or "[narrow question]",
        "IMPL_A": args.impl_a or "[implication A]",
        "IMPL_B": args.impl_b or "[implication B]",
        "PAPER": args.paper or "[paper/project]",
        "PARAPHRASE": args.paraphrase or "[one-sentence paraphrase]",
        "METHOD": args.method or "[dataset / comparative method]",
        "OBSERVATION": args.observation or "[provisional observation]",
        "HOURS": args.hours or "[X]",
        "NAME": args.name or "[Name]",
        "PROGRAMME": args.programme or "HKU BSocSc(Govt&Laws)&LLB",
        "JURISDICTION": args.jurisdiction or "[jurisdiction/development]",
        "PRACTICE": args.practice or "[practice point]",
    }
    for k, v in replacements.items():
        text = text.replace("{{" + k + "}}", v)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    return 0


def cmd_case_new(args: argparse.Namespace) -> int:
    tpl = (TEMPLATES / "case_object.md").read_text(encoding="utf-8")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = args.citation.lower().replace(" ", "-").replace("/", "-")[:80]
    path = out_dir / f"{slug}.md"
    content = tpl.replace("{{CITATION}}", args.citation)
    path.write_text(content, encoding="utf-8")
    print(f"Created {path}")
    return 0


def cmd_anki_export(args: argparse.Namespace) -> int:
    """Export simple TSV for Anki import from a markdown doctrine note or stdin cards file."""
    src = Path(args.source)
    lines = src.read_text(encoding="utf-8").splitlines()
    cards = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("Q:"):
            q = lines[i].strip()[2:].strip()
            a = ""
            i += 1
            if i < len(lines) and lines[i].strip().startswith("A:"):
                a = lines[i].strip()[2:].strip()
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("Q:"):
                    a += "<br>" + lines[i].strip()
                    i += 1
            cards.append((q, a))
        else:
            i += 1
    out = Path(args.out)
    with out.open("w", encoding="utf-8") as f:
        for q, a in cards:
            f.write(f"{q}\t{a}\n")
    print(f"Exported {len(cards)} cards → {out}")
    print("Anki: File → Import → select TSV → fields Front/Back")
    return 0


def cmd_score_log(args: argparse.Namespace) -> int:
    ensure_state()
    path = Path(args.scorecard)
    fieldnames = [
        "month", "timed_answers", "retrieval_sessions", "office_hours", "doctrine_graphs",
        "probability_problems", "coding_exercises", "simulations", "transactions_analysed",
        "conversations", "followups", "intros_made", "artifact_shipped", "runway_months", "notes",
    ]
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    row = {k: str(getattr(args, k, "") or "") for k in fieldnames}
    row["month"] = row["month"] or date.today().strftime("%Y-%m")
    # upsert by month
    rows = [r for r in rows if r.get("month") != row["month"]]
    rows.append(row)
    rows.sort(key=lambda r: r.get("month", ""))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Logged scorecard for {row['month']}")
    return 0


def cmd_app_track(args: argparse.Namespace) -> int:
    ensure_state()
    path = Path(args.apps)
    fieldnames = ["opportunity_id", "org", "programme", "status", "applied_on", "deadline", "notes"]
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if args.list:
        for r in rows:
            print(f"{r.get('status'):12} {r.get('org'):22} {r.get('programme')}")
        return 0
    opps = {o["id"]: o for o in load_opportunities(Path(args.data))}
    o = opps.get(args.id)
    if not o and not args.org:
        print(f"Unknown opportunity id: {args.id}", file=sys.stderr)
        return 1
    row = {
        "opportunity_id": args.id or "",
        "org": (o or {}).get("org") or args.org or "",
        "programme": (o or {}).get("programme") or args.programme or "",
        "status": args.status,
        "applied_on": args.applied_on or (date.today().isoformat() if args.status == "applied" else ""),
        "deadline": (o or {}).get("app_close") or "",
        "notes": args.notes or "",
    }
    rows = [r for r in rows if r.get("opportunity_id") != row["opportunity_id"]]
    rows.append(row)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Tracked {row['org']}: {row['status']}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    opps = load_opportunities(Path(args.data))
    today = date.today()
    ensure_state()
    critical_due = []
    for o in opps:
        if o.get("priority") not in {"critical", "committed"}:
            continue
        close = parse_date(o.get("app_close"))
        critical_due.append((close, o))
    critical_due.sort(key=lambda x: x[0] or date(2099, 1, 1))

    lines = [
        f"# Career OS Weekly Report — {today.isoformat()}",
        "",
        "## Immediate actions",
    ]
    for close, o in critical_due:
        if o.get("category") == "committed":
            lines.append(f"- LOCK DATES: {o['programme']} — {o.get('url')}")
            continue
        d = days_until(close, today) if close else None
        if d is not None and d < 0:
            continue
        lines.append(
            f"- [{o.get('priority')}] {o.get('org')}: {o.get('programme')} "
            f"(due {close or 'rolling'}, LIA={o.get('laidlaw_conflict')})"
        )
        if o.get("status_note"):
            lines.append(f"  - {o['status_note']}")
        lines.append(f"  - {o.get('url')}")

    lines += [
        "",
        "## Laidlaw rule",
        "Do not accept a full-time Jun–Aug 2027 internship overlapping your 6 LiA weeks without written Horizons approval.",
        "Prefer: Jane Street / Jump / Flow Traders Dec–Feb, Cleary & Reed Smith winter VS, SFC winter, AIIFL/LITE, Betatron part-time.",
        "",
        "## Counts",
        f"- Opportunities in database: {len(opps)}",
        f"- Laidlaw-compatible (conflict=none): {sum(1 for o in opps if o.get('laidlaw_conflict')=='none')}",
        f"- Likely summer conflict: {sum(1 for o in opps if o.get('laidlaw_conflict')=='likely')}",
    ]
    out = Path(args.out) if args.out else STATE / "weekly_report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))
    print(f"\nWrote {out}")
    return 0


def cmd_markdown_table(args: argparse.Namespace) -> int:
    opps = load_opportunities(Path(args.data))
    opps = sorted(opps, key=lambda o: (PRIORITY_ORDER.get(o.get("priority", "low"), 9), o.get("org", "")))
    lines = [
        "| Priority | Org | Programme | App close | Placement | LiA conflict | URL |",
        "|---|---|---|---|---|---|---|",
    ]
    kept = 0
    for o in opps:
        if args.laidlaw_safe and o.get("laidlaw_conflict") == "likely":
            continue
        kept += 1
        place = f"{o.get('placement_start') or '?'} → {o.get('placement_end') or '?'}"
        lines.append(
            f"| {o.get('priority')} | {o.get('org')} | {o.get('programme')} | "
            f"{o.get('app_close') or 'rolling'} | {place} | {o.get('laidlaw_conflict')} | "
            f"[link]({o.get('url')}) |"
        )
    out = Path(args.out) if args.out else STATE / "opportunities_table.md"
    ensure_state()
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({kept} rows)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="career-os", description="HKU Law capital-runway career automation")
    p.add_argument("--data", default=str(DEFAULT_OPP))
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("deadlines", help="List application deadlines")
    d.add_argument("--today", default=None)
    d.add_argument("--within-days", type=int, default=None)
    d.add_argument("--laidlaw-safe", action="store_true")
    d.add_argument("--include-rolling", action="store_true")
    d.add_argument("--category", nargs="*", default=None)
    d.add_argument("--priority", nargs="*", default=None)
    d.add_argument("--urls", action="store_true")
    d.set_defaults(func=cmd_deadlines)

    s = sub.add_parser("summer-plan", help="Laidlaw-aware Summer 2027 plan")
    s.add_argument("--profile", default=str(DEFAULT_PROFILE))
    s.add_argument("--out", default=None)
    s.add_argument("--urls", action="store_true")
    s.set_defaults(func=cmd_summer_plan)

    i = sub.add_parser("ics", help="Export deadline calendar .ics")
    i.add_argument("--out", default=None)
    i.add_argument("--laidlaw-safe", action="store_true")
    i.set_defaults(func=cmd_ics)

    cl = sub.add_parser("crm-list", help="List CRM contacts")
    cl.add_argument("--crm", default=str(DEFAULT_CRM))
    cl.set_defaults(func=cmd_crm_list)

    ca = sub.add_parser("crm-add", help="Add CRM contact")
    ca.add_argument("--crm", default=str(DEFAULT_CRM))
    ca.add_argument("--name", required=True)
    ca.add_argument("--org", required=True)
    ca.add_argument("--role-bucket", dest="role_bucket", default="associate")
    ca.add_argument("--practice", default="")
    ca.add_argument("--hook-url", dest="hook_url", default="")
    ca.add_argument("--relevant-proof", dest="relevant_proof", default="")
    ca.add_argument("--artifact", default="")
    ca.add_argument("--next-action", dest="next_action", default="")
    ca.add_argument("--status", default="researching")
    ca.add_argument("--notes", default="")
    ca.add_argument("--last-contact", dest="last_contact", default="")
    ca.set_defaults(func=cmd_crm_add)

    e = sub.add_parser("email", help="Render cold email from template")
    e.add_argument("--kind", choices=["partner", "professor", "followup"], default="partner")
    e.add_argument("--surname", default="")
    e.add_argument("--proof", default="")
    e.add_argument("--matter", default="")
    e.add_argument("--question", default="")
    e.add_argument("--impl-a", dest="impl_a", default="")
    e.add_argument("--impl-b", dest="impl_b", default="")
    e.add_argument("--paper", default="")
    e.add_argument("--paraphrase", default="")
    e.add_argument("--method", default="")
    e.add_argument("--observation", default="")
    e.add_argument("--hours", default="")
    e.add_argument("--name", default="")
    e.add_argument("--programme", default="")
    e.add_argument("--jurisdiction", default="")
    e.add_argument("--practice", default="")
    e.add_argument("--out", default=None)
    e.set_defaults(func=cmd_email)

    c = sub.add_parser("case-new", help="Create case object markdown")
    c.add_argument("--citation", required=True)
    c.add_argument("--out-dir", default=str(ROOT / "notes" / "cases"))
    c.set_defaults(func=cmd_case_new)

    a = sub.add_parser("anki-export", help="Export Q:/A: file to Anki TSV")
    a.add_argument("--source", required=True)
    a.add_argument("--out", default=str(STATE / "anki_import.tsv"))
    a.set_defaults(func=cmd_anki_export)

    sc = sub.add_parser("score-log", help="Log monthly scorecard")
    sc.add_argument("--scorecard", default=str(DEFAULT_SCORE))
    for field in [
        "month", "timed_answers", "retrieval_sessions", "office_hours", "doctrine_graphs",
        "probability_problems", "coding_exercises", "simulations", "transactions_analysed",
        "conversations", "followups", "intros_made", "artifact_shipped", "runway_months", "notes",
    ]:
        sc.add_argument(f"--{field.replace('_', '-')}", dest=field, default="")
    sc.set_defaults(func=cmd_score_log)

    ap = sub.add_parser("app-track", help="Track application status")
    ap.add_argument("--apps", default=str(DEFAULT_APPS))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--id", default="")
    ap.add_argument("--org", default="")
    ap.add_argument("--programme", default="")
    ap.add_argument("--status", default="researching", choices=["researching", "prep", "applied", "interview", "offer", "rejected", "withdrawn", "deferred_lia"])
    ap.add_argument("--applied-on", dest="applied_on", default="")
    ap.add_argument("--notes", default="")
    ap.set_defaults(func=cmd_app_track)

    r = sub.add_parser("report", help="Generate weekly action report")
    r.add_argument("--out", default=None)
    r.set_defaults(func=cmd_report)

    m = sub.add_parser("table", help="Export opportunities markdown table")
    m.add_argument("--out", default=None)
    m.add_argument("--laidlaw-safe", action="store_true")
    m.set_defaults(func=cmd_markdown_table)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
