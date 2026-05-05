from __future__ import annotations

from data import Audit, Assignment, Note, TeamMember, get_engine, session_scope
from helpers import week_keys


def seed_if_empty() -> bool:
    weeks = week_keys()
    with session_scope() as s:
        if s.query(Audit).first() is not None:
            return False

        members = [
            TeamMember(name="Adam Parker",   level="Director",     hours_per_week=40, email="adam.parker@walgreens.com"),
            TeamMember(name="Sarah Chen",    level="Manager",      hours_per_week=40, email="sarah.chen@walgreens.com"),
            TeamMember(name="James Wilson",  level="Senior Staff", hours_per_week=40),
            TeamMember(name="Maria Lopez",   level="Staff",        hours_per_week=40),
            TeamMember(name="David Kim",     level="Staff",        hours_per_week=40),
            TeamMember(name="Rachel Green",  level="Senior Staff", hours_per_week=40),
        ]
        for m in members:
            s.add(m)
        s.flush()
        by_name = {m.name: m for m in members}

        audits = [
            Audit(
                name="SOX Compliance Review - Revenue Cycle", phase="Fieldwork",
                start_week=weeks[2], end_week=weeks[14], budgeted_hours=480, type="SOX",
                risk_rating="High", likelihood=4, impact=4, completion_pct=35,
                owner="Sarah Chen", sponsor="CFO", business_unit="Finance",
                objectives="Evaluate design and operating effectiveness of SOX 404 controls over revenue recognition and accounts receivable.",
                scope="Revenue cycle including order-to-cash, credit management, and revenue recognition across retail and pharmacy segments. Period: FY2026 Q1-Q2.",
                workpaper_url="https://walgreens.sharepoint.com/sox-2026-revenue",
                assignments=[
                    Assignment(member_id=by_name["Sarah Chen"].id, hours_per_week=20),
                    Assignment(member_id=by_name["James Wilson"].id, hours_per_week=15),
                ],
                notes=[
                    Note(text="Kickoff meeting completed. Key controls identified across 4 business processes.", author="Adam Parker"),
                    Note(text="Testing sample selected: 25 items per control. Fieldwork on track.", author="Sarah Chen"),
                ],
            ),
            Audit(
                name="Vendor Risk Assessment - Top 50 Spend", phase="Planning",
                start_week=weeks[4], end_week=weeks[12], budgeted_hours=320, type="Third-Party",
                risk_rating="Medium", likelihood=3, impact=3, completion_pct=15,
                owner="Adam Parker", sponsor="CPO", business_unit="Supply Chain",
                objectives="Assess vendor risk posture for top-spend third parties with focus on data privacy, business continuity, and financial health.",
                scope="Top 50 vendors by annual spend ($500K+). Review SIG/SOC2 reports, insurance, and BCP documentation.",
                assignments=[
                    Assignment(member_id=by_name["Maria Lopez"].id, hours_per_week=25),
                ],
                notes=[
                    Note(text="Vendor universe pulled from SAP. 52 vendors meet threshold.", author="Adam Parker"),
                ],
            ),
            Audit(
                name="IT General Controls - Core Systems", phase="Pre-Planning",
                start_week=weeks[8], end_week=weeks[20], budgeted_hours=560, type="IT Audit",
                risk_rating="High", likelihood=4, impact=5, completion_pct=5,
                owner="James Wilson", sponsor="CTO", business_unit="IT",
                objectives="Evaluate IT general controls across SAP, Workday, and pharmacy dispensing systems.",
                scope="Change management, access controls, and computer operations for 3 core platforms.",
            ),
            Audit(
                name="Pharmacy Inventory Count Observation", phase="Complete",
                start_week=weeks[0], end_week=weeks[1], budgeted_hours=80, type="Operational",
                risk_rating="Medium", likelihood=3, impact=3, completion_pct=100,
                owner="Rachel Green", sponsor="COO", business_unit="Pharmacy",
                objectives="Observe physical inventory counts at sample pharmacy locations.",
                scope="10 sample locations across 3 regions.",
                assignments=[
                    Assignment(member_id=by_name["David Kim"].id, hours_per_week=20),
                    Assignment(member_id=by_name["Rachel Green"].id, hours_per_week=20),
                ],
                notes=[
                    Note(text="All observations complete. Final report issued.", author="Rachel Green"),
                ],
            ),
        ]
        for a in audits:
            s.add(a)
        return True


if __name__ == "__main__":
    get_engine()
    seeded = seed_if_empty()
    print("Seeded sample workspace." if seeded else "Workspace already populated.")
