from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable

WEEK_HOURS = 40
GREEN_THRESHOLD = 30
WEEKS_DISPLAY = 52

PHASES = ["Pre-Planning", "Planning", "Fieldwork", "Reporting", "Complete"]
LEVELS = ["Partner", "Director", "Manager", "Senior Staff", "Staff"]
RISK_LEVELS = ["Low", "Medium", "High", "Critical"]
AUDIT_TYPES = [
    "Control Testing", "SOX", "IT Audit", "Operational", "Financial",
    "Compliance", "Ad Hoc", "Advisory", "Fraud", "Regulatory",
    "Third-Party", "Follow-Up",
]
BUSINESS_UNITS = [
    "Retail Ops", "Pharmacy", "Supply Chain", "Finance", "HR", "IT",
    "Legal/Compliance", "Merchandising", "Real Estate", "Corporate",
]

HOLIDAYS = {
    "2025-01-20", "2025-02-17", "2025-05-26", "2025-06-19", "2025-07-04",
    "2025-09-01", "2025-10-13", "2025-11-11", "2025-11-27", "2025-11-28",
    "2025-12-24", "2025-12-25", "2025-12-31",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25", "2026-06-19",
    "2026-07-03", "2026-09-07", "2026-10-12", "2026-11-11", "2026-11-26",
    "2026-11-27", "2026-12-24", "2026-12-25", "2026-12-31",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-05-31", "2027-06-18",
    "2027-07-05", "2027-09-06", "2027-10-11", "2027-11-11", "2027-11-25",
    "2027-11-26", "2027-12-24", "2027-12-31",
}


def get_monday(d: date | None = None) -> date:
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def week_keys(start: date | None = None, count: int = WEEKS_DISPLAY) -> list[str]:
    monday = get_monday(start)
    return [(monday + timedelta(weeks=i)).isoformat() for i in range(count)]


def fmt_week(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.month}/{d.day}"


def month_label(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%b")


def is_holiday_week(iso: str) -> bool:
    start = date.fromisoformat(iso)
    for i in range(5):
        if (start + timedelta(days=i)).isoformat() in HOLIDAYS:
            return True
    return False


def max_hours_for_week(iso: str) -> int:
    return 32 if is_holiday_week(iso) else WEEK_HOURS


def risk_from_score(likelihood: int, impact: int) -> str:
    score = likelihood * impact
    if score >= 16:
        return "Critical"
    if score >= 10:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def weeks_between(start_iso: str, end_iso: str) -> int:
    s = date.fromisoformat(start_iso)
    e = date.fromisoformat(end_iso)
    return max(1, (e - s).days // 7 + 1)


def fmt_timestamp(iso: str | datetime) -> str:
    d = iso if isinstance(iso, datetime) else datetime.fromisoformat(iso.replace("Z", "+00:00"))
    today = datetime.now().date()
    if d.date() == today:
        return "Today " + d.strftime("%-I:%M %p")
    return d.strftime("%b %-d %-I:%M %p")


def weeks_in_audit(audit_start: str, audit_end: str, weeks: Iterable[str]) -> list[str]:
    return [w for w in weeks if audit_start <= w <= audit_end]


def member_week_hours(audits, members, weeks: list[str]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {m.id: {w: 0 for w in weeks} for m in members}
    for a in audits:
        for asgn in a.assignments:
            mid = asgn.member_id
            if mid not in out:
                continue
            for w in weeks:
                if a.start_week <= w <= a.end_week:
                    out[mid][w] = out[mid].get(w, 0) + (asgn.hours_per_week or 0)
    return out
