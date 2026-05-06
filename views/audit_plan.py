from __future__ import annotations

import streamlit as st

import data
import theme as T
from helpers import (
    AUDIT_TYPES, BUSINESS_UNITS, LEVELS, PHASES, RISK_LEVELS, WEEK_HOURS,
    fmt_week, member_week_hours, risk_from_score, week_keys, weeks_between,
)


def render(audits, members, activity, role: str) -> None:
    weeks = week_keys()
    is_editor = role == "editor"
    user = st.session_state.get("name", "Editor")

    # Top bar, search + filters + new audit
    top = st.columns([3, 2, 2, 2, 1, 1])
    search = top[0].text_input("Search", "", placeholder="Search audits…", label_visibility="collapsed")
    phase_filter = top[1].selectbox("Phase", ["All Phases", *PHASES], label_visibility="collapsed")
    risk_filter = top[2].selectbox("Risk", ["All Risk", *RISK_LEVELS], label_visibility="collapsed")
    bu_filter = top[3].selectbox("BU", ["All Business Units", *BUSINESS_UNITS], label_visibility="collapsed")

    if is_editor and top[5].button("＋ New", key="new_audit_top", type="primary", use_container_width=True):
        st.session_state["edit_audit_id"] = "__new__"
        st.rerun()

    filtered = [
        a for a in audits
        if (phase_filter == "All Phases" or a.phase == phase_filter)
        and (risk_filter == "All Risk" or a.risk_rating == risk_filter)
        and (bu_filter == "All Business Units" or a.business_unit == bu_filter)
        and (not search or search.lower() in a.name.lower())
    ]
    st.caption(f"{len(filtered)} of {len(audits)} audits")

    if not filtered:
        st.info("No audits match your filters.")

    for a in filtered:
        _render_audit_card(a, members, weeks, is_editor)

    # Modals (Streamlit dialogs)
    edit_id = st.session_state.get("edit_audit_id")
    if edit_id:
        _audit_edit_dialog(edit_id, members, weeks)

    assign_id = st.session_state.get("assign_audit_id")
    if assign_id:
        _assignment_dialog(assign_id, members, audits, weeks, user)

    detail_id = st.session_state.get("detail_audit_id")
    if detail_id:
        _detail_dialog(detail_id, is_editor, user)

    delete_id = st.session_state.get("delete_audit_id")
    if delete_id:
        _delete_audit_dialog(delete_id)



def _render_audit_card(a, members, weeks, is_editor: bool) -> None:
    weeks_in = weeks_between(a.start_week, a.end_week)
    allocated = sum(asgn.hours_per_week * weeks_in for asgn in a.assignments)
    over = allocated > a.budgeted_hours

    st.markdown(
        f'<div class="ledger-card" style="border-left:4px solid {T.RISK_COLOR[a.risk_rating]}">',
        unsafe_allow_html=True,
    )
    head = st.columns([4, 2])
    head[0].markdown(
        f'<div style="font-size:15px;font-weight:700;margin-bottom:6px">{T.safe(a.name)}</div>'
        f'<div>'
        f'{T.badge_html(a.phase, T.PHASE_COLOR[a.phase])}'
        f'{T.badge_html(a.risk_rating + " Risk", T.RISK_COLOR[a.risk_rating])}'
        f'{T.badge_html(T.safe(a.type), T.TEXT_MUTED)}'
        + (T.badge_html(T.safe(a.business_unit), T.TEXT_MUTED) if a.business_unit else "")
        + (T.badge_html(f"{len(a.notes)} Notes", T.TEXT_DIM) if a.notes else "")
        + "</div>",
        unsafe_allow_html=True,
    )
    btns = head[1].columns(4 if is_editor else 1)
    if btns[0].button("Details", key=f"det_{a.id}", use_container_width=True):
        st.session_state["detail_audit_id"] = a.id
        st.rerun()
    if is_editor:
        if btns[1].button("Assign", key=f"asg_{a.id}", use_container_width=True):
            st.session_state["assign_audit_id"] = a.id
            st.rerun()
        if btns[2].button("Edit", key=f"edt_{a.id}", use_container_width=True):
            st.session_state["edit_audit_id"] = a.id
            st.rerun()
        if btns[3].button("✕", key=f"del_{a.id}", help="Delete audit", use_container_width=True):
            st.session_state["delete_audit_id"] = a.id
            st.rerun()

    grid = st.columns(6)
    cells = [
        ("Timeline", f"{fmt_week(a.start_week)} → {fmt_week(a.end_week)}", False),
        ("Owner", T.safe(a.owner) or "-", False),
        ("Sponsor", T.safe(a.sponsor) or "-", False),
        ("Budget", f"{allocated}h / {a.budgeted_hours}h", over),
        ("Team", f"{len(a.assignments)} people", False),
        ("Progress", f"{a.completion_pct or 0}%", False),
    ]
    for col, (k, v, warn) in zip(grid, cells):
        col.markdown(
            f'<div style="font-size:10px;color:{T.TEXT_DIM};text-transform:uppercase;'
            f'font-weight:700;letter-spacing:0.5px;margin-bottom:4px">{k}</div>'
            f'<div style="font-size:13px;color:{T.DANGER if warn else T.TEXT}">{v}</div>',
            unsafe_allow_html=True,
        )

    st.progress(min(100, a.completion_pct or 0) / 100)

    if a.objectives:
        st.markdown(
            f'<div style="font-size:12px;color:{T.TEXT_MUTED};line-height:1.5;margin-top:10px;'
            f'padding-top:10px;border-top:1px solid {T.BORDER}">'
            f'<span style="color:{T.TEXT_DIM};font-weight:700;text-transform:uppercase;'
            f'font-size:10px;letter-spacing:0.5px">Objectives: </span>{T.safe(a.objectives)}</div>',
            unsafe_allow_html=True,
        )

    if a.assignments:
        chips = ""
        for asgn in a.assignments:
            m = next((x for x in members if x.id == asgn.member_id), None)
            if m:
                chips += (
                    f'<span style="display:inline-flex;gap:6px;align-items:center;'
                    f'background:{T.PAPER_ALT};border:1px solid {T.BORDER};border-radius:8px;'
                    f'padding:6px 10px;margin-right:6px;font-size:12px">'
                    f'<b>{T.safe(m.name)}</b><span style="color:{T.TEXT_DIM}">·</span>'
                    f'<span style="color:{T.PRIMARY};font-weight:700;font-family:Menlo,monospace">{asgn.hours_per_week}h/wk</span>'
                    f'</span>'
                )
        st.markdown(
            f'<div style="margin-top:10px;padding-top:10px;border-top:1px solid {T.BORDER}">'
            f'<div style="font-size:10px;color:{T.TEXT_DIM};text-transform:uppercase;'
            f'font-weight:700;letter-spacing:0.6px;margin-bottom:8px">Assigned Team</div>'
            f'{chips}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


@st.dialog("Edit audit", width="large")
def _audit_edit_dialog(audit_id: str, members, weeks):
    is_new = audit_id == "__new__"
    a = None if is_new else next((x for x in data.list_audits() if x.id == audit_id), None)
    if not is_new and a is None:
        st.error("Audit not found.")
        if st.button("Close"):
            st.session_state.pop("edit_audit_id", None)
            st.rerun()
        return

    st.markdown(f"### {'Add New Audit' if is_new else 'Edit Audit'}")

    with st.form("audit_form", clear_on_submit=False):
        name = st.text_input("Audit name", value="" if is_new else a.name)
        c1, c2 = st.columns(2)
        phase = c1.selectbox("Phase", PHASES, index=0 if is_new else PHASES.index(a.phase))
        type_ = c2.selectbox("Type", AUDIT_TYPES, index=0 if is_new else AUDIT_TYPES.index(a.type))

        c1, c2, c3 = st.columns(3)
        bu_options = ["-", *BUSINESS_UNITS]
        bu_default = 0 if is_new or not a.business_unit else bu_options.index(a.business_unit)
        bu = c1.selectbox("Business Unit", bu_options, index=bu_default)
        owner_options = ["-", *[m.name for m in members]]
        owner_default = 0 if is_new or not a.owner else (owner_options.index(a.owner) if a.owner in owner_options else 0)
        owner = c2.selectbox("Audit Owner", owner_options, index=owner_default)
        sponsor = c3.text_input("Business Sponsor", value="" if is_new else (a.sponsor or ""))

        c1, c2 = st.columns(2)
        likelihood = c1.slider("Likelihood", 1, 5, value=3 if is_new else a.likelihood)
        impact = c2.slider("Impact", 1, 5, value=3 if is_new else a.impact)
        risk = risk_from_score(likelihood, impact)
        st.markdown(
            f'<span style="font-size:11px;color:{T.TEXT_MUTED};text-transform:uppercase;'
            f'font-weight:700">Computed Risk: </span>'
            f'{T.badge_html(risk, T.RISK_COLOR[risk], solid=True)}'
            f'<span style="font-size:11px;color:{T.TEXT_DIM}"> · Score {likelihood * impact}</span>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        start_idx = 0 if is_new else (weeks.index(a.start_week) if a.start_week in weeks else 0)
        end_idx = 12 if is_new else (weeks.index(a.end_week) if a.end_week in weeks else 12)
        start = c1.selectbox("Start Week", weeks, index=start_idx, format_func=fmt_week)
        end = c2.selectbox("End Week", weeks, index=max(end_idx, weeks.index(start)), format_func=fmt_week)
        budget = c3.number_input("Budgeted Hours", min_value=0, value=200 if is_new else a.budgeted_hours, step=20)

        objectives = st.text_area("Objectives", value="" if is_new else (a.objectives or ""), height=80)
        scope = st.text_area("Scope", value="" if is_new else (a.scope or ""), height=80)
        workpaper = st.text_input("Workpapers URL", value="" if is_new else (a.workpaper_url or ""))

        save_col, cancel_col = st.columns([1, 1])
        save = save_col.form_submit_button("Save Changes" if not is_new else "Add Audit", type="primary", use_container_width=True)
        cancel = cancel_col.form_submit_button("Cancel", use_container_width=True)

    if cancel:
        st.session_state.pop("edit_audit_id", None)
        st.rerun()
    if save:
        if not name.strip():
            st.error("Name is required.")
            return
        fields = dict(
            name=name.strip(), phase=phase, type=type_,
            business_unit=None if bu == "-" else bu,
            owner=None if owner == "-" else owner,
            sponsor=sponsor.strip() or None,
            likelihood=likelihood, impact=impact, risk_rating=risk,
            start_week=start, end_week=end, budgeted_hours=int(budget),
            objectives=objectives.strip() or None, scope=scope.strip() or None,
            workpaper_url=workpaper.strip() or None,
        )
        if is_new:
            data.upsert_audit(None, **fields)
            data.log_activity("Added Audit", name, st.session_state.get("name", "Editor"))
        else:
            data.upsert_audit(audit_id, **fields)
            data.log_activity("Updated Audit", name, st.session_state.get("name", "Editor"))
        st.session_state.pop("edit_audit_id", None)
        st.rerun()


@st.dialog("Assign resources", width="large")
def _assignment_dialog(audit_id: str, members, audits, weeks, user: str):
    a = next((x for x in audits if x.id == audit_id), None)
    if a is None:
        st.error("Audit not found.")
        if st.button("Close"):
            st.session_state.pop("assign_audit_id", None)
            st.rerun()
        return

    weeks_in = weeks_between(a.start_week, a.end_week)
    initial = {asgn.member_id: asgn.hours_per_week for asgn in a.assignments}
    state_key = f"draft_{audit_id}"
    if state_key not in st.session_state:
        st.session_state[state_key] = dict(initial)
    draft = st.session_state[state_key]

    total = sum(h * weeks_in for h in draft.values())
    pct = round(total / a.budgeted_hours * 100) if a.budgeted_hours else 0
    is_dirty = draft != initial

    st.markdown(
        f'<div class="ledger-card" style="margin-bottom:12px">'
        f'<div style="font-size:15px;font-weight:700">{T.safe(a.name)}</div>'
        f'<div style="font-size:12px;color:{T.TEXT_MUTED}">{weeks_in}-week timeline · '
        f'{fmt_week(a.start_week)} → {fmt_week(a.end_week)}</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:10px">'
        f'<div><div style="font-size:10px;color:{T.TEXT_DIM};text-transform:uppercase;font-weight:700">Budget</div>'
        f'<div style="font-size:14px;font-weight:700;font-family:Menlo,monospace">{a.budgeted_hours}h</div></div>'
        f'<div><div style="font-size:10px;color:{T.TEXT_DIM};text-transform:uppercase;font-weight:700">Allocated</div>'
        f'<div style="font-size:14px;font-weight:700;font-family:Menlo,monospace;color:{T.DANGER if total > a.budgeted_hours else T.TEXT}">{total}h ({pct}%)</div></div>'
        f'<div><div style="font-size:10px;color:{T.TEXT_DIM};text-transform:uppercase;font-weight:700">Remaining</div>'
        f'<div style="font-size:14px;font-weight:700;font-family:Menlo,monospace;color:{T.DANGER if a.budgeted_hours - total < 0 else T.SUCCESS}">{a.budgeted_hours - total}h</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # Sort: assigned first (by hours desc), then by level
    sorted_members = sorted(
        members,
        key=lambda m: (
            0 if draft.get(m.id, 0) > 0 else 1,
            -draft.get(m.id, 0),
            LEVELS.index(m.level) if m.level in LEVELS else 99,
            m.name,
        ),
    )

    mwh = member_week_hours(audits, members, weeks)
    for m in sorted_members:
        hrs = draft.get(m.id, 0)
        is_assigned = hrs > 0
        bg = T.CARD if is_assigned else "#1a2332"
        name_color = T.TEXT if is_assigned else "#f6f2e9"
        sub_color = T.TEXT_MUTED if is_assigned else "#c9c0a8"
        border_color = f"{T.PRIMARY}44" if is_assigned else "#2d3d58"

        st.markdown(
            f'<div style="padding:10px 14px;background:{bg};border:1px solid {border_color};'
            f'border-radius:10px;margin-bottom:8px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;gap:14px">'
            f'<div><div style="font-size:13px;font-weight:700;color:{name_color}">{T.safe(m.name)}</div>'
            f'<div style="font-size:11px;color:{sub_color}">{T.safe(m.level)}'
            + ("" if is_assigned else " · <em>Available</em>")
            + "</div></div></div></div>",
            unsafe_allow_html=True,
        )
        new_hrs = st.slider(
            f"Hours/week, {m.name}", 0, 60, hrs,
            key=f"hrs_{audit_id}_{m.id}", label_visibility="collapsed",
        )
        if new_hrs != hrs:
            draft[m.id] = new_hrs
            if new_hrs <= 0:
                draft.pop(m.id, None)
            st.rerun()
        load_other = mwh.get(m.id, {}).get(weeks[0], 0) - (initial.get(m.id, 0) if a.start_week <= weeks[0] <= a.end_week else 0)
        load_total = load_other + (new_hrs if a.start_week <= weeks[0] <= a.end_week else 0)
        over_msg = ", overloaded" if load_total > WEEK_HOURS else ""
        st.caption(f"Week load: {load_total}h / {WEEK_HOURS}h{over_msg} · Total on audit: {new_hrs * weeks_in}h")

    st.write("")
    bcols = st.columns([4, 1, 1])
    bcols[0].caption(
        f"{sum(1 for v in draft.values() if v > 0)} of {len(members)} assigned"
        + (" · unsaved changes" if is_dirty else "")
    )
    if bcols[1].button("Cancel", use_container_width=True, key=f"asg_cancel_{audit_id}"):
        if is_dirty:
            st.session_state["confirm_close_assign"] = audit_id
            st.rerun()
        else:
            st.session_state.pop(state_key, None)
            st.session_state.pop("assign_audit_id", None)
            st.rerun()
    if bcols[2].button("Apply Changes", use_container_width=True, type="primary",
                       disabled=not is_dirty, key=f"asg_apply_{audit_id}"):
        data.replace_assignments(audit_id, [(mid, hrs) for mid, hrs in draft.items() if hrs > 0])
        data.log_activity("Updated Assignments", f"{sum(1 for v in draft.values() if v > 0)} on {a.name}", user)
        st.session_state.pop(state_key, None)
        st.session_state.pop("assign_audit_id", None)
        st.rerun()

    if st.session_state.get("confirm_close_assign") == audit_id:
        st.warning("**Discard unsaved assignments?** Your changes will be lost.")
        c1, c2 = st.columns(2)
        if c1.button("Keep editing", use_container_width=True, key=f"keep_{audit_id}"):
            st.session_state.pop("confirm_close_assign", None)
            st.rerun()
        if c2.button("Discard", use_container_width=True, type="primary", key=f"discard_{audit_id}"):
            st.session_state.pop(state_key, None)
            st.session_state.pop("assign_audit_id", None)
            st.session_state.pop("confirm_close_assign", None)
            st.rerun()


@st.dialog("Audit details", width="large")
def _detail_dialog(audit_id: str, can_edit: bool, user: str):
    a = data.get_audit(audit_id)
    if a is None:
        st.error("Audit not found.")
        if st.button("Close"):
            st.session_state.pop("detail_audit_id", None)
            st.rerun()
        return

    st.markdown(f"### {T.safe(a.name)}")
    st.markdown(
        T.badge_html(a.phase, T.PHASE_COLOR[a.phase])
        + T.badge_html(f"{a.risk_rating} Risk (L{a.likelihood} × I{a.impact})", T.RISK_COLOR[a.risk_rating])
        + T.badge_html(T.safe(a.type), T.TEXT_MUTED)
        + (T.badge_html(T.safe(a.business_unit), T.TEXT_MUTED) if a.business_unit else "")
        + T.badge_html(f"Owner: {T.safe(a.owner) or '-'}", T.TEXT_MUTED)
        + (T.badge_html(f"Sponsor: {T.safe(a.sponsor)}", T.TEXT_MUTED) if a.sponsor else ""),
        unsafe_allow_html=True,
    )

    tab_overview, tab_notes = st.tabs(["Overview", f"Notes ({len(a.notes)})"])

    with tab_overview:
        for label, value, placeholder in [
            ("Objectives", a.objectives,
             "To be announced, objectives will be drafted during the planning phase."),
            ("Scope", a.scope,
             "To be announced, in-scope and out-of-scope boundaries are still being defined."),
        ]:
            filled = bool(value and value.strip())
            border = f"1px solid {T.BORDER}" if filled else f"1px dashed {T.BORDER_LIGHT}"
            display_value = T.safe(value) if filled else placeholder
            st.markdown(
                f'<div style="margin-bottom:18px"><div style="font-size:11px;color:{T.TEXT_MUTED};'
                f'text-transform:uppercase;font-weight:700;letter-spacing:0.8px;margin-bottom:8px">{label}</div>'
                f'<div style="font-size:14px;color:{T.TEXT if filled else T.TEXT_DIM};line-height:1.7;'
                f'padding:18px 22px;background:{T.PAPER_ALT};border-radius:10px;border:{border};'
                f'font-style:{"normal" if filled else "italic"};white-space:pre-wrap">{display_value}</div></div>',
                unsafe_allow_html=True,
            )
   
        st.markdown(f'<div style="font-size:11px;color:{T.TEXT_MUTED};text-transform:uppercase;'
                    f'font-weight:700;letter-spacing:0.8px;margin-bottom:8px">Workpapers</div>',
                    unsafe_allow_html=True)
        if a.workpaper_url:
            url = a.workpaper_url
            if url.startswith(("http://", "https://")):
                st.markdown(f"[Open workpaper folder ↗]({url})")
            else:
                st.caption("Workpaper URL must start with http:// or https://")
        else:
            st.markdown(
                f'<div style="font-size:14px;color:{T.TEXT_DIM};font-style:italic;'
                f'padding:18px 22px;background:{T.PAPER_ALT};border-radius:10px;'
                f'border:1px dashed {T.BORDER_LIGHT}">'
                f'To be announced, link a SharePoint or Teams workpaper folder once created.</div>',
                unsafe_allow_html=True,
            )

        st.markdown("**Completion**")
        if can_edit:
            new_pct = st.slider("Completion %", 0, 100, a.completion_pct or 0, key=f"pct_{a.id}")
            if new_pct != (a.completion_pct or 0):
                data.update_completion(a.id, new_pct)
                data.log_activity("Updated Completion", f"{new_pct}% on {a.name}", user)
                st.rerun()
        else:
            st.progress((a.completion_pct or 0) / 100)
            st.caption(f"{a.completion_pct or 0}%")

    with tab_notes:
        if can_edit:
            with st.form(f"note_{a.id}", clear_on_submit=True):
                txt = st.text_area("Add a note", placeholder="Status update, finding, or context…", label_visibility="collapsed")
                if st.form_submit_button("＋ Add note", type="primary"):
                    if txt.strip():
                        data.add_note(a.id, txt.strip(), user)
                        data.log_activity("Added Note", f"on {a.name}", user)
                        st.rerun()
        for n in sorted(a.notes, key=lambda n: n.timestamp, reverse=True):
            cols = st.columns([6, 1])
            cols[0].markdown(
                f'<div style="padding:10px 0;border-bottom:1px solid {T.BORDER}">'
                f'<div style="font-size:12px;color:{T.TEXT_MUTED}">'
                f'<b style="color:{T.TEXT}">{n.author}</b> · {n.timestamp.strftime("%b %d, %-I:%M %p")}</div>'
                f'<div style="font-size:13px;line-height:1.6;margin-top:4px;white-space:pre-wrap">{n.text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if can_edit and cols[1].button("✕", key=f"delnote_{n.id}"):
                data.delete_note(n.id)
                st.rerun()
        if not a.notes:
            st.caption("No notes yet.")


@st.dialog("Delete audit?")
def _delete_audit_dialog(audit_id: str):
    a = next((x for x in data.list_audits() if x.id == audit_id), None)
    if a is None:
        st.session_state.pop("delete_audit_id", None)
        st.rerun()
        return
    st.markdown(
        f"**“{a.name}”** will be permanently removed from the plan, along with its "
        f"assignments and notes. This cannot be undone."
    )
    c1, c2 = st.columns(2)
    if c1.button("Cancel", use_container_width=True):
        st.session_state.pop("delete_audit_id", None)
        st.rerun()
    if c2.button("Delete audit", use_container_width=True, type="primary"):
        data.delete_audit(audit_id)
        data.log_activity("Deleted Audit", a.name, st.session_state.get("name", "Editor"))
        st.session_state.pop("delete_audit_id", None)
        st.rerun()
