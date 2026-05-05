from __future__ import annotations

import streamlit as st

import theme as T
from exports.workbooks import (
    activity_log_xlsx, audit_plan_xlsx, executive_xlsx,
    team_roster_xlsx, utilization_xlsx,
)
from helpers import member_week_hours, week_keys


def render(audits, members, activity, role: str) -> None:
    weeks = week_keys()
    mwh = member_week_hours(audits, members, weeks)

    st.markdown(
        f'<div class="ledger-card" style="margin-bottom:18px;display:flex;gap:14px;align-items:flex-start">'
        f'<div style="width:44px;height:44px;border-radius:10px;background:{T.ACCENT}1c;'
        f'border:1px solid {T.ACCENT}55;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0">'
        f'<span style="color:{T.ACCENT};font-size:20px;font-weight:700">⤓</span></div>'
        f'<div><h3 style="margin:0">Export center</h3>'
        f'<p style="margin:4px 0 0;font-size:13px;color:{T.TEXT_MUTED};line-height:1.5">'
        f'Excel workbooks ready for the Audit Committee, header banding, frozen panes, '
        f'color-coded status cells, number formatting. No CSVs here; the heatmap and '
        f'multi-sheet exports rely on formatting CSV cannot carry.</p></div></div>',
        unsafe_allow_html=True,
    )

    cards = [
        ("Audit Plan",
         "Every audit with phase, risk, owner, allocated vs. budgeted hours, and objectives.",
         "audit-plan.xlsx",
         lambda: audit_plan_xlsx(audits, members)),
        ("Team Roster",
         "Members with this-week load, annual hours, current status, and assigned audits.",
         "team-roster.xlsx",
         lambda: team_roster_xlsx(members, audits, mwh, weeks)),
        ("52-Week Utilization",
         "Heatmap workbook with month banding, week-by-week hours, team totals, and available capacity.",
         "utilization-52wk.xlsx",
         lambda: utilization_xlsx(members, mwh, weeks)),
        ("Executive Summary",
         "Audit Committee–ready report: traffic-light status by audit, plus a Business Unit breakdown sheet.",
         "executive-summary.xlsx",
         lambda: executive_xlsx(audits, members)),
        ("Activity Log",
         "Full audit trail of every change made to this workspace, sorted newest first.",
         "activity-log.xlsx",
         lambda: activity_log_xlsx(activity)),
    ]

    cols = st.columns(2)
    for i, (title, desc, fname, builder) in enumerate(cards):
        with cols[i % 2]:
            st.markdown('<div class="ledger-card">', unsafe_allow_html=True)
            st.markdown(f"#### {title}")
            st.markdown(f'<p style="font-size:12px;color:{T.TEXT_MUTED};line-height:1.55">{desc}</p>',
                        unsafe_allow_html=True)
            st.download_button(
                label=f"⤓  Download {fname}",
                data=builder(),
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{fname}",
                use_container_width=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

