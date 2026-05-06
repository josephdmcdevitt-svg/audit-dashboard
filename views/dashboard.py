from __future__ import annotations

import pandas as pd
import streamlit as st

import theme as T
from helpers import (
    GREEN_THRESHOLD, PHASES, WEEK_HOURS, fmt_week, max_hours_for_week,
    member_week_hours, month_label, week_keys, weeks_between,
)


def render(audits, members, activity, role: str) -> None:
    weeks = week_keys()
    mwh = member_week_hours(audits, members, weeks)
    current_week = weeks[0]

    active = [a for a in audits if a.phase != "Complete"]
    complete = [a for a in audits if a.phase == "Complete"]
    total_budget = sum(a.budgeted_hours for a in audits)
    total_allocated = sum(
        sum(asgn.hours_per_week * weeks_between(a.start_week, a.end_week) for asgn in a.assignments)
        for a in audits
    )
    avg_completion = round(sum(a.completion_pct or 0 for a in active) / len(active)) if active else 0
    critical_high = sum(1 for a in audits if a.risk_rating in ("Critical", "High"))

    overloaded = [m for m in members if mwh.get(m.id, {}).get(current_week, 0) > WEEK_HOURS]
    on_track = [m for m in members if GREEN_THRESHOLD <= mwh.get(m.id, {}).get(current_week, 0) <= WEEK_HOURS]
    available = [m for m in members if mwh.get(m.id, {}).get(current_week, 0) < GREEN_THRESHOLD]

    # KPI row
    cols = st.columns(6)
    kpis = [
        ("Active Audits", len(active), f"{len(complete)} complete this period", T.PRIMARY),
        ("Team Members", len(members), "", T.PRIMARY),
        ("Critical/High Risk", critical_high, f"{len(audits)} total audits", T.DANGER),
        ("Avg Completion", f"{avg_completion}%", "", T.SUCCESS if avg_completion > 50 else T.WARNING),
        ("Capacity", f"{round(total_allocated / total_budget * 100) if total_budget else 0}%",
         f"{total_allocated:,}h / {total_budget:,}h",
         T.DANGER if total_allocated > total_budget else T.PRIMARY),
        ("This Week", f"{len(overloaded)} over",
         f"{len(on_track)} utilized · {len(available)} available", T.DANGER if overloaded else T.SUCCESS),
    ]
    for col, (label, value, sub, color) in zip(cols, kpis):
        col.markdown(T.kpi_html(label, value, sub, color), unsafe_allow_html=True)

    st.write("")

    # Mid row: Active engagements + capacity + pipeline
    left, mid, right = st.columns([2, 1, 1])

    with left:
        st.markdown('<div class="ledger-card">', unsafe_allow_html=True)
        st.markdown("#### Audit Status, Active Engagements")
        if not active:
            st.caption("No active audits.")
        for a in active:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:8px 0;border-bottom:1px solid {T.BORDER}">'
                f'<div style="display:flex;gap:10px;align-items:center">'
                f'<div style="width:4px;height:30px;border-radius:2px;background:{T.RISK_COLOR[a.risk_rating]}"></div>'
                f'<div><div style="font-weight:600;color:{T.TEXT}">{T.safe(a.name)}</div>'
                f'<div style="font-size:11px;color:{T.TEXT_MUTED};margin-top:2px">'
                f'{a.phase} · {T.safe(a.owner) or "Unassigned"} · {a.risk_rating} risk</div></div></div>'
                f'<div style="font-family:Menlo,monospace;font-size:13px;font-weight:700;color:{T.PRIMARY}">'
                f'{a.completion_pct or 0}%</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with mid:
        st.markdown('<div class="ledger-card">', unsafe_allow_html=True)
        st.markdown("#### This Week Capacity")
        if overloaded:
            st.markdown(T.badge_html(f"Overloaded · {len(overloaded)}", T.DANGER), unsafe_allow_html=True)
            for m in overloaded:
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;font-size:12px;color:{T.DANGER};padding:3px 0">'
                    f'<span>{T.safe(m.name)}</span><span style="font-family:Menlo,monospace">{mwh[m.id][current_week]}h</span></div>',
                    unsafe_allow_html=True,
                )
        if on_track:
            st.markdown(T.badge_html(f"Utilized · {len(on_track)}", T.WARNING), unsafe_allow_html=True)
            for m in on_track:
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;font-size:12px;color:{T.TEXT_MUTED};padding:3px 0">'
                    f'<span>{T.safe(m.name)}</span><span style="font-family:Menlo,monospace">{mwh[m.id][current_week]}h</span></div>',
                    unsafe_allow_html=True,
                )
        if available:
            st.markdown(T.badge_html(f"Available · {len(available)}", T.SUCCESS), unsafe_allow_html=True)
            for m in available:
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;font-size:12px;color:{T.TEXT_MUTED};padding:3px 0">'
                    f'<span>{T.safe(m.name)}</span><span style="color:{T.SUCCESS};font-family:Menlo,monospace">'
                    f'{WEEK_HOURS - mwh[m.id][current_week]}h free</span></div>',
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="ledger-card">', unsafe_allow_html=True)
        st.markdown("#### Pipeline")
        for phase in PHASES:
            count = sum(1 for a in audits if a.phase == phase)
            pct = round(count / len(audits) * 100) if audits else 0
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">'
                f'<div style="width:118px;flex-shrink:0">'
                f'{T.badge_html(phase, T.PHASE_COLOR[phase])}</div>'
                f'<div style="flex:1;min-width:0;height:6px;background:{T.PAPER_ALT};border-radius:3px;overflow:hidden">'
                f'<div style="width:{pct}%;height:100%;background:{T.PHASE_COLOR[phase]}"></div></div>'
                f'<div style="font-family:Menlo,monospace;font-size:12px;font-weight:700;min-width:24px;text-align:right">{count}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    if overloaded:
        st.error(
            f"**Capacity alert**, {len(overloaded)} team member"
            f"{'s are' if len(overloaded) > 1 else ' is'} over {WEEK_HOURS}h this week."
        )

    # 52-week heatmap
    st.markdown("### 52-Week Resource Capacity")
    st.caption(f"Starting {fmt_week(weeks[0])}")
    df = _build_utilization_df(members, mwh, weeks)
    st.dataframe(df, use_container_width=True, hide_index=False, height=min(60 + 38 * (len(members) + 2), 600))



def _build_utilization_df(members, mwh, weeks):
    cols = [(month_label(w), fmt_week(w), w) for w in weeks]
    multiindex = pd.MultiIndex.from_tuples([(m, w) for m, w, _ in cols], names=["Month", "Week"])
    rows = []
    index = []
    for m in members:
        index.append(f"{m.name}  ({m.level})")
        rows.append([mwh.get(m.id, {}).get(w, 0) for _, _, w in cols])

    # Totals + available
    week_totals = [sum(mwh.get(m.id, {}).get(w, 0) for m in members) for _, _, w in cols]
    week_avail = [len(members) * max_hours_for_week(w) - week_totals[i] for i, (_, _, w) in enumerate(cols)]
    index += ["Team Total", "Available Capacity"]
    rows += [week_totals, week_avail]

    df = pd.DataFrame(rows, index=index, columns=multiindex)

    def color_cell(v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return ""
        if v > WEEK_HOURS:
            return f"background-color:#e6c2bb;color:{T.DANGER_DEEP};font-weight:700"
        if v > WEEK_HOURS * 0.85:
            return f"background-color:#e8d4a8;color:#8b6423"
        if v >= GREEN_THRESHOLD:
            return "background-color:#c8d0dd"
        if v > 0:
            return "background-color:#c8d6cb"
        return f"color:{T.TEXT_DIM}"

    styler = df.style.format("{:.0f}").map(color_cell)
    return styler
